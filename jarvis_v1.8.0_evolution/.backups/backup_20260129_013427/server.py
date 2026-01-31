"""
JARVIS 服务器
"""
import os
import sys
import json
import asyncio
import signal
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse
from agent import run_agent
from llm import call_llm, load_secrets
from pydantic import BaseModel
from self_modify import get_or_create_session, clear_session, request_restart
from openai import OpenAI

app = FastAPI()

# 重启标记文件
RESTART_FILE = ".restart_requested"


class Msg(BaseModel):
    message: str
    images: list[str] = []  # 图片列表（base64或URL）


class ModifyRequest(BaseModel):
    filename: str
    content: str = None
    test_code: str = None


@app.get("/")
def home():
    return FileResponse("ui_v2.html")


def _build_user_message(text: str, images: list[str]):
    """构建用户消息，支持图片"""
    if not images:
        return text
    
    # 构建多模态消息
    content = [{"type": "text", "text": text}]
    
    for img in images:
        if img.startswith("http://") or img.startswith("https://"):
            # URL格式
            content.append({
                "type": "image_url",
                "image_url": {"url": img}
            })
        else:
            # 假设是base64格式
            if not img.startswith("data:image"):
                img = f"data:image/png;base64,{img}"
            content.append({
                "type": "image_url",
                "image_url": {"url": img}
            })
    
    return content


@app.post("/run")
def run(m: Msg):
    """
    智能路由（使用 Function Calling）：
    1. 调用 DeepSeek，让模型判断是否需要工具
    2. 如果不需要工具 → 直接返回对话结果
    3. 如果需要工具 → 走 agent 规划执行流程
    """
    user_input = m.message.strip()
    
    # 定义 agent 工具
    tools = [
        {
            "type": "function",
            "function": {
                "name": "execute_task",
                "description": "执行具体任务，如读写文件、运行命令、扫描项目、分析代码、操作Git等。当用户需要你执行具体操作时调用此工具。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_description": {
                            "type": "string",
                            "description": "用户的任务描述"
                        }
                    },
                    "required": ["task_description"]
                }
            }
        }
    ]
    
    try:
        # 尝试使用 Ollama R1:14b（本地优先）
        try:
            print("[SERVER] trying local ollama for function calling")
            client = OpenAI(
                api_key="ollama",
                base_url="http://localhost:11434/v1"
            )
            response = client.chat.completions.create(
                model="deepseek-r1:14b",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是 JARVIS，一个智能助理。\n"
                            "你可以进行对话，也可以执行具体任务（读写文件、运行命令、扫描项目等）。\n"
                            "如果用户只是问候、闲聊、询问你的能力，直接回复即可。\n"
                            "如果用户需要你执行具体操作，调用 execute_task 工具。\n"
                            "生成代码时不要写注释，保持代码简洁。"
                        )
                    },
                    {"role": "user", "content": _build_user_message(user_input, m.images)}
                ],
                tools=tools,
                tool_choice="auto",
                temperature=0.3
            )
            print("[SERVER] local ollama succeeded")
            message = response.choices[0].message
            
            if message.tool_calls:
                return {"result": run_agent(user_input)}
            else:
                return {"result": "CHAT_MODE", "response": message.content}
                
        except Exception as e:
            print(f"[SERVER] local ollama failed: {e}, fallback to DeepSeek API")
        
        # 降级到 DeepSeek API
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
                    "content": (
                        "你是 JARVIS，一个智能助理。\n"
                        "你可以进行对话，也可以执行具体任务（读写文件、运行命令、扫描项目等）。\n"
                        "如果用户只是问候、闲聊、询问你的能力，直接回复即可。\n"
                        "如果用户需要你执行具体操作，调用 execute_task 工具。\n"
                        "生成代码时不要写注释，保持代码简洁。"
                    )
                },
                {"role": "user", "content": _build_user_message(user_input, m.images)}
            ],
            tools=tools,
            tool_choice="auto",
            temperature=0.3
        )
        
        message = response.choices[0].message
        
        # 检查是否需要调用工具
        if message.tool_calls:
            # 需要工具 → 走 agent 流程
            return {"result": run_agent(user_input)}
        else:
            # 纯对话 → 直接返回
            return {
                "result": "CHAT_MODE",
                "response": message.content
            }
            
    except Exception as e:
        print(f"[SERVER] Function calling 失败: {e}")
        # 降级：直接走 agent 流程
        return {"result": run_agent(user_input)}


@app.get("/events")
def events():
    try:
        return json.load(open("EVENTS.json", encoding="utf-8"))
    except Exception:
        return []


@app.get("/health")
def health():
    # 检查是否有重启请求
    restart_pending = os.path.exists(RESTART_FILE)
    return {
        "status": "ok",
        "version": "3.2",
        "restart_pending": restart_pending
    }


@app.get("/report")
def report():
    try:
        return json.load(open("REPORT.json", encoding="utf-8"))
    except Exception:
        return {"error": "No report available"}


# ==================== 自我修改相关端点 ====================

@app.post("/self-modify/start")
def start_modify_session():
    """启动自我修改会话"""
    try:
        session = get_or_create_session()
        success, msg = session.start_session()
        return {"success": success, "message": msg, "session_id": session.session_id}
    except Exception as e:
        return {"success": False, "message": str(e)}


@app.get("/self-modify/status")
def get_modify_status():
    """获取自我修改会话状态"""
    try:
        session = get_or_create_session()
        return session.get_session_status()
    except Exception as e:
        return {"error": str(e)}


@app.post("/self-modify/read")
def read_temp_file(req: ModifyRequest):
    """读取临时目录中的文件"""
    try:
        session = get_or_create_session()
        success, content = session.read_temp_file(req.filename)
        return {"success": success, "content": content}
    except Exception as e:
        return {"success": False, "content": str(e)}


@app.post("/self-modify/modify")
def modify_temp_file(req: ModifyRequest):
    """修改临时目录中的文件"""
    try:
        session = get_or_create_session()
        success, msg = session.modify_temp_file(req.filename, req.content)
        return {"success": success, "message": msg}
    except Exception as e:
        return {"success": False, "message": str(e)}


@app.post("/self-modify/test")
def run_tests(req: ModifyRequest = None):
    """运行测试"""
    try:
        session = get_or_create_session()
        
        if req and req.test_code:
            # 运行自定义测试
            success, msg = session.run_custom_test(req.test_code)
        else:
            # 运行所有标准测试
            success, msg = session.run_all_tests()
        
        return {"success": success, "message": msg}
    except Exception as e:
        return {"success": False, "message": str(e)}


@app.post("/self-modify/apply")
def apply_modifications(force: bool = False):
    """应用修改"""
    try:
        session = get_or_create_session()
        success, msg = session.apply_modifications(force=force)
        return {"success": success, "message": msg}
    except Exception as e:
        return {"success": False, "message": str(e)}


@app.post("/self-modify/rollback")
def rollback_modifications():
    """回滚修改"""
    try:
        session = get_or_create_session()
        success, msg = session.rollback()
        return {"success": success, "message": msg}
    except Exception as e:
        return {"success": False, "message": str(e)}


@app.post("/self-modify/end")
def end_modify_session(cleanup: bool = True):
    """结束自我修改会话"""
    try:
        session = get_or_create_session()
        success, msg = session.end_session(cleanup=cleanup)
        clear_session()
        return {"success": success, "message": msg}
    except Exception as e:
        return {"success": False, "message": str(e)}


@app.post("/self-modify/restart")
def request_server_restart(background_tasks: BackgroundTasks):
    """请求重启服务器"""
    try:
        success, msg = request_restart()
        
        if success:
            # 在后台执行重启
            background_tasks.add_task(perform_restart)
        
        return {"success": success, "message": msg}
    except Exception as e:
        return {"success": False, "message": str(e)}


async def perform_restart():
    """执行重启"""
    await asyncio.sleep(2)  # 等待响应发送完成
    
    # 删除重启标记文件
    if os.path.exists(RESTART_FILE):
        os.remove(RESTART_FILE)
    
    # 发送 SIGTERM 信号给自己，让 uvicorn 重启
    os.kill(os.getpid(), signal.SIGTERM)


# ==================== 启动时检查 ====================

@app.on_event("startup")
async def startup_event():
    """服务器启动时的检查"""
    # 清理可能残留的重启标记
    if os.path.exists(RESTART_FILE):
        os.remove(RESTART_FILE)
    
    print("🤖 JARVIS v3.2 已启动")
    print("   - Function Calling 智能路由已启用")
    print("   - 安全自我修改功能已启用")


# ==================== 启动服务器 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
