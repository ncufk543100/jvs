"""
JARVIS 服务器 (v1.5.2)
支持跨平台路径处理与安全自我修改。
"""
import os
import sys
import json
import asyncio
import signal
from pathlib import Path
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from openai import OpenAI

# 导入跨平台工具
from platform_compatibility import normalize_path, is_windows
from agent import run_agent
from llm import call_llm, load_secrets
from self_modify import get_or_create_session, clear_session, request_restart

app = FastAPI()

# 获取项目根目录
_ROOT = Path(__file__).parent.absolute()
RESTART_FILE = normalize_path(_ROOT / ".restart_requested")

class Msg(BaseModel):
    message: str
    images: list[str] = []

class ModifyRequest(BaseModel):
    filename: str
    content: str = None
    test_code: str = None

@app.get("/")
def home():
    ui_path = normalize_path(_ROOT / "ui_v2.html")
    if not os.path.exists(ui_path):
        # 兼容旧版本文件名
        ui_path = normalize_path(_ROOT / "ui.html")
    return FileResponse(ui_path)

def _build_user_message(text: str, images: list[str]):
    if not images: return text
    content = [{"type": "text", "text": text}]
    for img in images:
        if img.startswith("http"):
            content.append({"type": "image_url", "image_url": {"url": img}})
        else:
            if not img.startswith("data:image"):
                img = f"data:image/png;base64,{img}"
            content.append({"type": "image_url", "image_url": {"url": img}})
    return content

@app.post("/run")
def run(m: Msg):
    user_input = m.message.strip()
    tools = [{
        "type": "function",
        "function": {
            "name": "execute_task",
            "description": "执行具体任务，如读写文件、运行命令、扫描项目等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_description": {"type": "string", "description": "用户的任务描述"}
                },
                "required": ["task_description"]
            }
        }
    }]
    
    try:
        # 降级到 DeepSeek API (简化逻辑，优先保证稳定性)
        secrets = load_secrets()
        client = OpenAI(
            api_key=secrets.get("deepseek_api_key"),
            base_url=secrets.get("deepseek_base_url")
        )
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": "你是 JARVIS，一个智能助理。如果用户需要执行具体操作，调用 execute_task 工具。"
                },
                {"role": "user", "content": _build_user_message(user_input, m.images)}
            ],
            tools=tools,
            tool_choice="auto",
            temperature=0.3
        )
        
        message = response.choices[0].message
        if message.tool_calls:
            return {"result": run_agent(user_input)}
        else:
            return {"result": "CHAT_MODE", "response": message.content}
            
    except Exception as e:
        print(f"[SERVER] 路由失败: {e}")
        return {"result": run_agent(user_input)}

@app.get("/events")
def events():
    path = normalize_path(_ROOT / "EVENTS.json")
    try:
        return json.load(open(path, encoding="utf-8"))
    except:
        return []

@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "1.5.2",
        "platform": "Windows" if is_windows() else "Linux",
        "restart_pending": os.path.exists(RESTART_FILE)
    }

# ==================== 自我修改相关端点 ====================

@app.post("/self-modify/start")
def start_modify_session():
    success, msg = get_or_create_session().start_session()
    return {"success": success, "message": msg}

@app.post("/self-modify/modify")
def modify_temp_file(req: ModifyRequest):
    success, msg = get_or_create_session().modify_temp_file(req.filename, req.content)
    return {"success": success, "message": msg}

@app.post("/self-modify/test")
def run_tests():
    success, msg = get_or_create_session().run_shadow_server_test()
    return {"success": success, "message": msg}

@app.post("/self-modify/apply")
def apply_modifications(force: bool = False):
    success, msg = get_or_create_session().apply_modifications(force=force)
    return {"success": success, "message": msg}

@app.post("/self-modify/restart")
def request_server_restart(background_tasks: BackgroundTasks):
    success, msg = request_restart()
    if success: background_tasks.add_task(perform_restart)
    return {"success": success, "message": msg}

async def perform_restart():
    await asyncio.sleep(1)
    if os.path.exists(RESTART_FILE): os.remove(RESTART_FILE)
    os.kill(os.getpid(), signal.SIGTERM if not is_windows() else signal.CTRL_C_EVENT)

@app.on_event("startup")
async def startup_event():
    if os.path.exists(RESTART_FILE): os.remove(RESTART_FILE)
    print(f"🤖 JARVIS v1.5.2 已启动 (Platform: {'Windows' if is_windows() else 'Linux'})")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
