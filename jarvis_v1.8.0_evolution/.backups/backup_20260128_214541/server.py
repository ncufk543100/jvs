"""
ClawedBot 服务器
"""
import os
import sys
import json
import asyncio
import signal
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse
from agent import run_agent
from pydantic import BaseModel
from self_modify import get_or_create_session, clear_session, request_restart

app = FastAPI()

# 重启标记文件
RESTART_FILE = ".restart_requested"


class Msg(BaseModel):
    message: str


class ModifyRequest(BaseModel):
    filename: str
    content: str = None
    test_code: str = None


@app.get("/")
def home():
    return FileResponse("ui.html")


@app.post("/run")
def run(m: Msg):
    return {"result": run_agent(m.message)}


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
        "version": "3.1",
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
    
    print("🤖 ClawedBot v3.1 已启动")
    print("   - 安全自我修改功能已启用")
    print("   - 访问 /self-modify/start 开始自我修改会话")
