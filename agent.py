"""
JARVIS 智能代理模块 (v1.7.1) - 工具觉醒版
"""
import json
import threading
import re
import time
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any

# 导入跨平台工具
from platform_compatibility import normalize_path, is_windows
from llm import think, chat
from executor import execute, get_available_tools_with_meta
from run_lock import acquire, release
from safe_io import safe_write_json, safe_read_json
from event_bus import emit

# 文件路径归一化
_ROOT = Path(__file__).parent.absolute()
STATE_FILE = normalize_path(_ROOT / "STATE.json")
PLAN_FILE = normalize_path(_ROOT / "PLAN.json")
MEMORY_FILE = normalize_path(_ROOT / "CHAT_MEMORY.json")

# 配置
MAX_ITERATIONS = 10

def load_memory() -> dict:
    default = {"history": [], "context": {}}
    return safe_read_json(MEMORY_FILE, default=default)

def create_dynamic_plan(goal: str, memory: dict) -> dict:
    """根据用户目标制定计划"""
    tools_with_meta = get_available_tools_with_meta()
    tools_desc = json.dumps(tools_with_meta, ensure_ascii=False, indent=2)
    
    prompt = f"""你是一个智能代理。请分析用户目标并制定执行计划。
可用工具：
{tools_desc}

用户目标：
{goal}

请务必只返回 JSON 格式的计划，格式如下：
{{
    "understanding": "对目标的理解",
    "steps": [
        {{"tool": "工具名", "params": {{"参数名": "值"}}, "description": "步骤描述"}}
    ]
}}
"""
    try:
        response = think(prompt)
        # 增强 JSON 提取逻辑，处理 R1 可能带有的 Markdown 标签
        json_match = re.search(r'(\{[\s\S]*\})', response)
        if json_match:
            return json.loads(json_match.group(1))
    except Exception as e:
        print(f"[PLAN] 失败: {e}")
    return {"understanding": goal, "steps": []}

def run_agent(goal: str) -> str:
    """运行智能代理"""
    if not acquire():
        return "⚠️ 另一个任务正在运行中..."
    
    try:
        emit("status", f"🚀 贾维斯启动")
        iteration = 0
        
        while iteration < MAX_ITERATIONS:
            iteration += 1
            emit("status", f"📋 正在进行第 {iteration} 次尝试...")
            
            plan = create_dynamic_plan(goal, {})
            steps = plan.get("steps", [])
            
            if not steps:
                # 如果没有步骤，直接对话回复
                response = chat(goal)
                emit("assistant", response)
                return response
            
            for step in steps:
                tool = step.get("tool")
                params = step.get("params", {})
                desc = step.get("description", "")
                
                emit("thinking", f"🛠️ 执行: {desc}")
                result = execute(f"RUN {json.dumps({'tool': tool, 'params': params})}")
                emit("status", f"✅ 完成: {tool}")
                
            # 简单逻辑：执行完所有步骤后，生成最终回复
            final_prompt = f"用户目标：{goal}\n执行结果：已完成上述步骤。请给用户一个最终回复。"
            response = chat(final_prompt)
            emit("assistant", response)
            return response
            
        return "任务达到最大迭代次数。"
    except Exception as e:
        error_msg = f"❌ 异常: {str(e)}"
        emit("error", error_msg)
        return error_msg
    finally:
        release()
