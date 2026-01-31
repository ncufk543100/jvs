import json
import re
import time
import os
import sys
import hashlib
from llm import think, chat
from executor import execute, get_available_tools_with_meta
from run_lock import acquire, release
from knowledge_base import save_experience, get_relevant_knowledge

def run_agent(goal: str) -> str:
    """
    JARVIS v3.1.0 "Sovereign": 集成 OpenClaw 核心灵魂的自主进化引擎。
    """
    if len(goal.strip()) <= 4:
        return chat(f"用户指令：'{goal}'。请以贾维斯身份询问具体需求。")

    if not acquire(): return "⚠️ 任务占用中"
    
    # 初始化任务上下文
    iteration = 0
    max_iterations = 20
    history_steps = []
    
    print(f"\n🌟 [JARVIS v3.1.0 启动] 目标: {goal}")
    
    try:
        while iteration < max_iterations:
            iteration += 1
            print(f"\n🚀 [第 {iteration}/{max_iterations} 轮自主迭代]")
            
            # 1. 检索历史经验 (OpenClaw 核心逻辑)
            relevant_exp = get_relevant_knowledge(goal)
            
            # 2. 构建增强型 Prompt
            tools_desc = json.dumps(get_available_tools_with_meta(), ensure_ascii=False)
            prompt = f"""
### 任务目标
{goal}

### 历史经验参考 (来自 KNOWLEDGE_BASE)
{relevant_exp}

### 当前可用工具 (含已学习技能)
{tools_desc}

### 行为准则
1. 观察：在执行写操作前，先观察目录结构和文件状态。
2. 反思：如果连续失败，必须在 reflection 中分析原因并更换工具或路径。
3. 进化：如果任务复杂，尝试使用 learn_skill 封装新能力。

请返回 JSON 格式：
{{
  "thought": "当前局势深度分析",
  "reflection": "对上一轮行动的反思（若是第一轮则写规划）",
  "steps": [{{"tool": "...", "params": {{}}, "description": "..."}}],
  "is_finished": false
}}
"""
            try:
                raw_response = think(prompt)
                json_match = re.search(r'(\{[\s\S]*\})', raw_response)
                if not json_match: continue
                
                plan = json.loads(json_match.group(1))
                thought = plan.get("thought", "")
                reflection = plan.get("reflection", "")
                steps = plan.get("steps", [])
                
                print(f"🧠 思考: {thought}")
                print(f"📝 反思: {reflection}")
                
                if plan.get("is_finished"):
                    print("🏁 贾维斯判定任务已完美达成。")
                    save_experience(goal, history_steps, True, reflection)
                    break
                
                # 3. 执行并记录
                for step in steps:
                    desc = step.get("description", "执行操作")
                    print(f"🛠️ 执行: {desc}")
                    result = execute(f"RUN {json.dumps(step)}")
                    
                    step_record = {"tool": step.get("tool"), "desc": desc, "result": result}
                    history_steps.append(step_record)
                    
                    # 将执行结果反馈给下一轮
                    relevant_exp += f"\n最近操作({desc}): {result}"

            except Exception as e:
                print(f"⚠️ 运行异常: {e}")
                time.sleep(2)
                
        if iteration >= max_iterations:
            print("🚨 达到理智熔断上限。")
            save_experience(goal, history_steps, False, "任务超时，未能完成。")
            
        # 4. 生成结项报告
        report_prompt = f"任务结束。目标: {goal}\n过程记录: {json.dumps(history_steps[-10:], ensure_ascii=False)}\n请向用户汇报。"
        final_report = chat(report_prompt)
        print(f"\n🤖 贾维斯: {final_report}")
        return final_report
        
    finally:
        release()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_agent(" ".join(sys.argv[1:]))
