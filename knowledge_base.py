"""
JARVIS 知识图谱模块 (v1.7.5)
核心功能：
- 经验条 (Experience Fragments) 存储与检索
- 自动总结任务成功/失败模式
- 为 Agent 提供历史决策参考
"""
import json
import os
import time
from pathlib import Path
from typing import List, Dict, Any
from safe_io import safe_write_json, safe_read_json
from platform_compatibility import normalize_path

_ROOT = Path(__file__).parent.absolute()
KB_FILE = normalize_path(_ROOT / "KNOWLEDGE_BASE.json")

def load_kb() -> Dict[str, Any]:
    """加载知识库"""
    default = {
        "experiences": [],
        "tool_insights": {},
        "error_patterns": {},
        "last_updated": None
    }
    return safe_read_json(KB_FILE, default=default)

def save_experience(goal: str, steps: List[Dict], success: bool, reflection: str = ""):
    """保存一次任务经验"""
    kb = load_kb()
    experience = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "goal": goal,
        "success": success,
        "steps_count": len(steps),
        "reflection": reflection,
        "key_steps": [s.get("tool") for s in steps[:5]] # 记录关键路径
    }
    kb["experiences"].append(experience)
    # 只保留最近 200 条经验
    if len(kb["experiences"]) > 200:
        kb["experiences"] = kb["experiences"][-200:]
    
    kb["last_updated"] = experience["timestamp"]
    safe_write_json(KB_FILE, kb)

def get_relevant_knowledge(goal: str) -> str:
    """检索与当前目标相关的知识"""
    kb = load_kb()
    if not kb["experiences"]:
        return "暂无相关历史经验。"
    
    # 简单的关键词匹配（未来可升级为向量检索）
    relevant = []
    keywords = goal.split()
    for exp in kb["experiences"][-50:]: # 检索最近50条
        if any(kw.lower() in exp["goal"].lower() for kw in keywords if len(kw) > 1):
            status = "✅ 成功" if exp["success"] else "❌ 失败"
            relevant.append(f"- [{status}] 目标: {exp['goal']}\n  反思: {exp['reflection']}")
    
    if not relevant:
        return "未发现直接相关的历史经验。"
    
    return "\n".join(relevant[:5]) # 返回前5条相关经验

def update_tool_insight(tool_name: str, insight: str):
    """更新对某个工具的深度见解"""
    kb = load_kb()
    if tool_name not in kb["tool_insights"]:
        kb["tool_insights"][tool_name] = []
    kb["tool_insights"][tool_name].append({
        "date": time.strftime("%Y-%m-%d"),
        "insight": insight
    })
    safe_write_json(KB_FILE, kb)

def get_tool_insights(tool_name: str) -> List[str]:
    """获取工具的深度见解"""
    kb = load_kb()
    insights = kb["tool_insights"].get(tool_name, [])
    return [i["insight"] for i in insights[-3:]] # 返回最近3条
