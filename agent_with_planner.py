"""
JARVIS Agent with Structured Planner (v2.1.0)
集成结构化规划系统的智能代理
"""

import json
import uuid
from event_bus import emit
from executor import execute
from agent import validate_tool_params
from llm import chat
from run_lock import acquire, release
from planner import Planner, TaskPlan

MAX_ITERATIONS = 10

class JarvisAgentWithPlanner:
    """集成结构化规划的JARVIS智能代理"""
    
    def __init__(self):
        self.version = "2.1.0"
        self.current_plan: TaskPlan = None
    
    def run(self, goal: str) -> str:
        """
        运行智能代理 - v2.1.0 with Structured Planner
        
        Args:
            goal: 任务目标
        
        Returns:
            str: 执行结果
        """
        acquire()
        task_id = str(uuid.uuid4())[:8]
        
        try:
            emit("status", "贾维斯 v2")
            
            # 1. 创建结构化任务计划
            planner = Planner()
            complexity = planner.analyze_complexity(goal)
            self.current_plan = planner.create_plan(goal, complexity)
            
            emit("plan_info", f"📋 任务计划已创建（{complexity}级，{len(self.current_plan.phases)}个阶段）")
            
            # 2. 逐阶段执行
            while self.current_plan.current_phase_id <= len(self.current_plan.phases):
                current_phase = self.current_plan.get_current_phase()
                if not current_phase:
                    break
                
                emit("phase_start", f"🎯 阶段 {current_phase.id}/{len(self.current_plan.phases)}: {current_phase.title}")
                emit("phase_desc", f"   {current_phase.description}")
                
                # 执行当前阶段
                success = self.execute_phase(current_phase, goal)
                
                if success:
                    # 推进到下一阶段
                    if not self.current_plan.advance():
                        # 所有阶段完成
                        break
                else:
                    # 阶段失败
                    error_msg = current_phase.error or "未知错误"
                    emit("error", f"❌ 阶段 {current_phase.id} 失败: {error_msg}")
                    return f"任务失败于阶段 {current_phase.id}: {current_phase.title}"
            
            # 3. 保存计划
            self.current_plan.save()
            
            final_msg = f"✅ 任务完成！共执行 {len(self.current_plan.phases)} 个阶段。"
            emit("assistant", final_msg)
            return final_msg
            
        except Exception as e:
            error_msg = f"❌ 异常: {str(e)}"
            emit("error", error_msg)
            return error_msg
        finally:
            release()
    
    def execute_phase(self, phase, goal: str) -> bool:
        """
        执行单个阶段
        
        Args:
            phase: Phase对象
            goal: 任务目标
        
        Returns:
            bool: 是否成功
        """
        # 生成当前阶段的具体执行步骤
        phase_goal = f"{goal} - 当前阶段: {phase.title} ({phase.description})"
        
        try:
            # 使用LLM生成当前阶段的执行计划
            # 判断是否需要工具执行
            thinking_phases = ["需求分析", "可行性分析", "架构设计", "方案设计"]
            
            if phase.title in thinking_phases:
                # 纯思考阶段，不需要工具
                prompt = f"""
任务目标: {goal}

当前阶段: {phase.title}
阶段描述: {phase.description}

请对这个阶段进行深入分析和思考，直接输出你的分析结果。
"""
                response = chat(prompt)
                # 将思考过程发送到对话区
                emit("assistant", f"### {phase.title}\n\n{response}")
                phase.result = response
                return True
            
            # 需要工具执行的阶段
            prompt = f"""
任务目标: {goal}

当前阶段: {phase.title}
阶段描述: {phase.description}

请为这个阶段生成具体的执行步骤。返回JSON格式:
{{
  "steps": [
    {{"tool": "工具名", "params": {{}}, "description": "步骤描述"}}
  ]
}}

可用工具及参数格式:
1. write_file: {{"path": "/home/ubuntu/jarvis/文件名", "content": "文件内容"}}
2. read_file: {{"path": "/home/ubuntu/jarvis/文件名"}}
3. run_shell: {{"command": "shell命令"}}

注意:
- 必须提供所有必需参数
- path必须以 /home/ubuntu/jarvis/ 开头
- 如果不需要使用工具，可以返回空数组
"""
            
            response = chat(prompt)
            
            # 尝试解析JSON
            try:
                # 提取JSON部分
                if "```json" in response:
                    json_str = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    json_str = response.split("```")[1].split("```")[0].strip()
                else:
                    json_str = response.strip()
                
                plan = json.loads(json_str)
                steps = plan.get("steps", [])
            except (json.JSONDecodeError, IndexError):
                # 如果无法解析，直接返回LLM响应
                emit("thinking", f"💭 {response}")
                phase.result = response
                return True
            
            # 执行步骤
            if not steps:
                emit("thinking", f"💭 {response}")
                phase.result = response
                return True
            
            success_count = 0
            for step in steps:
                tool = step.get("tool")
                params = step.get("params", {})
                desc = step.get("description", "")
                
                # 参数验证
                valid, error_msg = validate_tool_params(tool, params)
                if not valid:
                    emit("status", f"⚠️ {error_msg}")
                    phase.error = error_msg
                    return False
                
                emit("thinking", f"🛠️ 执行: {desc}")
                result = execute(f"RUN {json.dumps({'tool': tool, 'params': params})}")
                
                # 检查错误
                result_str = str(result)
                if result_str.startswith(('错误：', '执行失败', '执行异常', '读取失败', '写入失败', '未知工具', '参数验证失败')):
                    emit("status", f"⚠️ 步骤失败: {tool}")
                    phase.error = result_str
                    return False
                else:
                    success_count += 1
                    emit("status", f"✅ 完成: {tool}")
            
            phase.result = f"成功执行 {success_count} 个步骤"
            return True
            
        except Exception as e:
            phase.error = str(e)
            emit("error", f"❌ 阶段执行异常: {str(e)}")
            return False

def run_agent_with_planner(goal: str):
    """JARVIS Agent with Planner 入口函数"""
    agent = JarvisAgentWithPlanner()
    return agent.run(goal)

# 测试
if __name__ == "__main__":
    result = run_agent_with_planner("创建一个简单的Python脚本计算1+1")
    print(f"\n最终结果: {result}")
