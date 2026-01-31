import json
import os
from safe_io import safe_read_json, safe_write_json

KNOWLEDGE_BASE_FILE = "KNOWLEDGE_BASE.json"

def save_experience(goal, steps, success, reflection):
    data = safe_read_json(KNOWLEDGE_BASE_FILE, {"experiences": []})
    experience = {
        "goal": goal,
        "steps": steps,
        "success": success,
        "reflection": reflection,
        "timestamp": os.path.getmtime(KNOWLEDGE_BASE_FILE) if os.path.exists(KNOWLEDGE_BASE_FILE) else 0
    }
    data["experiences"].append(experience)
    safe_write_json(KNOWLEDGE_BASE_FILE, data)

def get_relevant_knowledge(goal):
    # 简单的实现：返回最近的3条经验
    data = safe_read_json(KNOWLEDGE_BASE_FILE, {"experiences": []})
    
    # 过滤成功的经验，并按时间倒序
    successful_experiences = [
        exp for exp in data["experiences"] if exp["success"]
    ]
    
    # 简单的相关性匹配（实际OpenClaw会用向量搜索）
    relevant = sorted(
        successful_experiences,
        key=lambda x: goal.lower() in x["goal"].lower(),
        reverse=True
    )
    
    if not relevant:
        return "无相关历史经验。"
        
    summary = "相关历史经验:\n"
    for i, exp in enumerate(relevant[:3]):
        summary += f"- 经验 {i+1} (目标: {exp['goal']}): {exp['reflection']}\n"
        
    return summary
