"""
ClawedBot 记忆管理器
支持多轮对话记忆、上下文理解、任务历史
"""
import json
import os
from datetime import datetime
from safe_io import safe_write_json

MEMORY_FILE = "CHAT_MEMORY.json"
LONG_MEM_FILE = "LONG_MEMORY.json"
MAX_HISTORY = 50  # 最多保存的对话轮数
MAX_CONTEXT_LENGTH = 5000  # 上下文最大字符数


def load_memory():
    """加载记忆"""
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "history": [],
            "context": {},
            "user_preferences": {},
            "task_history": [],
            "created_at": datetime.now().isoformat()
        }


def save_memory(memory):
    """保存记忆"""
    memory["updated_at"] = datetime.now().isoformat()
    safe_write_json(MEMORY_FILE, memory)


def load_long_memory():
    """加载长期记忆"""
    try:
        with open(LONG_MEM_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"common_errors": [], "tool_usage": {}}


def save_long_memory(m):
    """保存长期记忆"""
    safe_write_json(LONG_MEM_FILE, m)


def remember_error(error):
    """记录错误"""
    m = load_long_memory()
    if "common_errors" not in m:
        m["common_errors"] = []
    m["common_errors"].append({
        "error": str(error),
        "timestamp": datetime.now().isoformat()
    })
    # 限制错误记录数量
    if len(m["common_errors"]) > 100:
        m["common_errors"] = m["common_errors"][-100:]
    save_long_memory(m)


def remember_tool(tool):
    """记录工具使用"""
    m = load_long_memory()
    if "tool_usage" not in m:
        m["tool_usage"] = {}
    m["tool_usage"][tool] = m["tool_usage"].get(tool, 0) + 1
    save_long_memory(m)


def add_conversation(user_input: str, assistant_response: str, tools_used: list = None):
    """添加对话记录"""
    memory = load_memory()
    
    conversation = {
        "timestamp": datetime.now().isoformat(),
        "user": user_input,
        "assistant": assistant_response,
        "tools_used": tools_used or []
    }
    
    memory["history"].append(conversation)
    
    # 限制历史记录数量
    if len(memory["history"]) > MAX_HISTORY:
        memory["history"] = memory["history"][-MAX_HISTORY:]
    
    save_memory(memory)


def add_task_result(task: str, result: str, success: bool):
    """添加任务执行结果"""
    memory = load_memory()
    
    task_record = {
        "timestamp": datetime.now().isoformat(),
        "task": task,
        "result": result,
        "success": success
    }
    
    if "task_history" not in memory:
        memory["task_history"] = []
    
    memory["task_history"].append(task_record)
    
    # 限制任务历史数量
    if len(memory["task_history"]) > 100:
        memory["task_history"] = memory["task_history"][-100:]
    
    save_memory(memory)


def get_context_summary(max_length: int = MAX_CONTEXT_LENGTH) -> str:
    """获取上下文摘要，用于 LLM 理解历史"""
    memory = load_memory()
    
    if not memory.get("history"):
        return "这是新对话，没有历史记录。"
    
    # 获取最近的对话
    recent = memory["history"][-10:]
    
    summary_parts = ["最近的对话历史:"]
    total_length = 0
    
    for conv in reversed(recent):
        entry = f"\n用户: {conv['user'][:200]}\n助手: {conv['assistant'][:300]}"
        if total_length + len(entry) > max_length:
            break
        summary_parts.append(entry)
        total_length += len(entry)
    
    return "\n".join(summary_parts)


def get_recent_tasks(count: int = 5) -> list:
    """获取最近的任务"""
    memory = load_memory()
    return memory.get("task_history", [])[-count:]


def update_user_preference(key: str, value):
    """更新用户偏好"""
    memory = load_memory()
    
    if "user_preferences" not in memory:
        memory["user_preferences"] = {}
    
    memory["user_preferences"][key] = value
    save_memory(memory)


def get_user_preference(key: str, default=None):
    """获取用户偏好"""
    memory = load_memory()
    return memory.get("user_preferences", {}).get(key, default)


def set_context(key: str, value):
    """设置上下文变量"""
    memory = load_memory()
    
    if "context" not in memory:
        memory["context"] = {}
    
    memory["context"][key] = {
        "value": value,
        "timestamp": datetime.now().isoformat()
    }
    save_memory(memory)


def get_context(key: str, default=None):
    """获取上下文变量"""
    memory = load_memory()
    ctx = memory.get("context", {}).get(key, {})
    return ctx.get("value", default)


def clear_history():
    """清除对话历史"""
    memory = load_memory()
    memory["history"] = []
    save_memory(memory)
    return "对话历史已清除"


def get_stats() -> dict:
    """获取记忆统计"""
    memory = load_memory()
    long_mem = load_long_memory()
    return {
        "total_conversations": len(memory.get("history", [])),
        "total_tasks": len(memory.get("task_history", [])),
        "tool_usage": long_mem.get("tool_usage", {}),
        "error_count": len(long_mem.get("common_errors", [])),
        "created_at": memory.get("created_at", "未知"),
        "updated_at": memory.get("updated_at", "未知")
    }
