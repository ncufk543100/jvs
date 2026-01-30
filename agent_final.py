"""
JARVIS Agent Final (v2.3.0)
集成所有能力的最终版本

Phase 1-3: 基础能力、意图推断、动态进化
Phase 4: 用户反馈学习、跨任务迁移、知识图谱、持续进化
工具管理: 工具清单、能力自省、外部工具发现、工具创造决策
"""

import json
import uuid
import time
from datetime import datetime
from event_bus import emit
from executor import execute
from agent import validate_tool_params
from llm import chat
from run_lock import acquire, release
from planner import Planner, TaskPlan

# Phase 4 模块
from feedback_learner import get_learner
from transfer_learning import get_transfer_learner
from knowledge_graph import get_knowledge_graph
from evolution_loop import get_evolution_loop

# 工具管理模块
from tool_registry import get_registry
from capability_introspection import get_introspection
from external_tool_discovery import get_discovery
from tool_creation_decision import get_decision

# 自我优化模块
from self_optimizer import get_self_optimizer
from error_logger import get_error_logger
from resilience_engine import get_resilience_engine

MAX_ITERATIONS = 10

class JarvisAgentFinal:
    """最终完整的JARVIS智能代理"""
    
    def __init__(self):
        self.version = "2.3.0"
        self.current_plan: TaskPlan = None
        
        # Phase 4 组件
        self.learner = get_learner()
        self.transfer_learner = get_transfer_learner()
        self.knowledge_graph = get_knowledge_graph()
        self.evolution_loop = get_evolution_loop()
        
        # 工具管理组件
        self.registry = get_registry()
        self.introspection = get_introspection()
        self.discovery = get_discovery()
        self.decision = get_decision()
        
        # 自我优化组件
        self.optimizer = get_self_optimizer()
        self.error_logger = get_error_logger()
        self.resilience = get_resilience_engine()
        
        # 当前任务追踪
        self.current_task_id = None
        self.current_task_start_time = None
        self.current_task_tools_used = []
    
    def run(self, goal: str) -> str:
        """
        运行智能代理 - v2.3.0 Final
        
        Args:
            goal: 任务目标
        
        Returns:
            str: 执行结果
        """
        acquire()
        self.current_task_id = str(uuid.uuid4())[:8]
        self.current_task_start_time = time.time()
        self.current_task_tools_used = []
        
        try:
            emit("status", "贾维斯 v2")
            
            # === 阶段0: 自我认知和准备 ===
            emit("assistant", "## 🤔 自我认知\n\n正在评估我的能力...")
            
            # 1. 能力自省：我能做这个任务吗？
            capability_check = self.introspection.can_i_do_this(goal)
            
            emit("assistant", f"### 能力评估\n\n"
                             f"- **可行性**: {'✅ 可以完成' if capability_check['can_do'] else '❌ 无法完成'}\n"
                             f"- **置信度**: {capability_check['confidence']:.1%}\n"
                             f"- **理由**: {capability_check['reasoning']}\n")
            
            if not capability_check['can_do']:
                # 无法完成任务
                emit("error", f"❌ 任务超出我的能力范围")
                return f"抱歉，{capability_check['reasoning']}"
            
            # 2. 工具需求分析
            if capability_check['missing_tools']:
                emit("assistant", f"### 缺失工具\n\n"
                                 f"需要但缺失的工具：{', '.join([f'`{t}`' for t in capability_check['missing_tools']])}\n")
                
                # 3. 工具创造决策
                tool_decision = self.decision.should_i_create_tool(goal)
                
                if tool_decision['should_create']:
                    emit("assistant", f"### 工具创造决策\n\n"
                                     f"**决定**: 创造新工具\n"
                                     f"**理由**: {tool_decision['reason']}\n"
                                     f"**工具规格**: `{tool_decision['tool_spec']['name']}`\n")
                    
                    # 自动创造工具
                    creation_result = self.decision.create_tool_from_spec(tool_decision['tool_spec'])
                    
                    if creation_result['success']:
                        emit("assistant", f"✅ {creation_result['message']}")
                    else:
                        emit("assistant", f"⚠️ {creation_result['message']}，将使用替代方案")
                else:
                    emit("assistant", f"### 工具创造决策\n\n"
                                     f"**决定**: 不创造新工具\n"
                                     f"**理由**: {tool_decision['reason']}\n"
                                     f"**替代方案**: {tool_decision['alternative']}\n")
            
            # 4. 检查跨任务迁移经验
            recommendation = self.transfer_learner.recommend_strategy(goal)
            if recommendation:
                emit("assistant", f"### 💡 迁移学习建议\n\n"
                                 f"{recommendation['reason']}\n\n"
                                 f"- **推荐策略**: `{recommendation['strategy']}`\n"
                                 f"- **推荐工具**: {', '.join([f'`{t}`' for t in recommendation['tools']])}\n"
                                 f"- **置信度**: {recommendation['confidence']:.1%}\n")
            
            # 5. 获取最佳策略
            best_strategy = self.learner.get_best_strategy()
            emit("assistant", f"### 📊 当前最优策略\n\n`{best_strategy}`\n")
            
            # === 阶段1: 创建结构化任务计划 ===
            emit("assistant", "## 📋 任务规划\n\n正在创建结构化任务计划...")
            
            planner = Planner()
            complexity = planner.analyze_complexity(goal)
            self.current_plan = planner.create_plan(goal, complexity)
            
            emit("plan_info", f"已创建 {len(self.current_plan.phases)} 阶段的任务计划 ({complexity}级)")
            
            # 添加任务到知识图谱
            self.knowledge_graph.add_entity(
                self.current_task_id,
                "task",
                {"goal": goal, "complexity": complexity}
            )
            
            # === 阶段2: 逐阶段执行 ===
            emit("assistant", "## 🚀 开始执行\n")
            
            iteration = 0
            while self.current_plan.current_phase_id <= len(self.current_plan.phases):
                current_phase = self.current_plan.get_current_phase()
                if not current_phase:
                    break
                
                iteration += 1
                emit("phase_start", f"🎯 阶段 {current_phase.id}/{len(self.current_plan.phases)}: {current_phase.title}")
                
                # 执行当前阶段
                success = self.execute_phase(current_phase, goal)
                
                if success:
                    # 推进到下一阶段
                    if not self.current_plan.advance():
                        break
                else:
                    # 阶段失败
                    error_msg = current_phase.error or "未知错误"
                    
                    # 记录到知识图谱
                    error_id = f"error_{self.current_task_id}_{current_phase.id}"
                    self.knowledge_graph.add_entity(
                        error_id,
                        "error",
                        {"message": error_msg, "phase": current_phase.title}
                    )
                    self.knowledge_graph.add_relation(
                        self.current_task_id,
                        "encountered",
                        error_id
                    )
                    
                    emit("error", f"⚠️ 阶段 {current_phase.id}/{len(self.current_plan.phases)}: {current_phase.title}")
                    emit("assistant", f"**失败原因**: {error_msg}")
                    
                    # 记录失败
                    self._record_task_completion(
                        success=False,
                        iterations=iteration,
                        error_msg=error_msg
                    )
                    
                    return f"任务失败于阶段 {current_phase.id}: {current_phase.title}"
            
            # === 阶段3: 完成和总结 ===
            self.current_plan.save()
            
            # 记录成功
            self._record_task_completion(
                success=True,
                iterations=iteration
            )
            
            final_msg = f"任务执行完成。共迭代 {iteration} 次。"
            emit("assistant", f"## ✅ 任务完成\n\n{final_msg}")
            
            return final_msg
            
        except Exception as e:
            error_msg = f"异常: {str(e)}"
            emit("error", f"❌ {error_msg}")
            
            # 记录异常
            self._record_task_completion(
                success=False,
                iterations=0,
                error_msg=error_msg
            )
            
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
        phase_goal = f"{goal} - 当前阶段: {phase.title} ({phase.description})"
        
        try:
            # 判断是否需要工具执行
            needs_tools = any(keyword in phase.title.lower() for keyword in [
                "创建", "编写", "执行", "测试", "部署", "修改", "分析文件"
            ])
            
            if needs_tools:
                # 需要工具执行
                # 获取可用工具列表
                available_tools = self.registry.list_tools()
                tool_descriptions = "\n".join([
                    f"{i+1}. {tool.name}: {tool.description}"
                    for i, tool in enumerate(available_tools)
                ])
                
                prompt = f"""
你是JARVIS，正在执行任务的一个阶段。

**任务目标**: {goal}
**当前阶段**: {phase.title}
**阶段描述**: {phase.description}

**可用工具**:
{tool_descriptions}

请生成本阶段需要执行的步骤。

工具参数格式:
1. write_file: {{"path": "/home/ubuntu/jarvis/文件名", "content": "文件内容"}}
2. read_file: {{"path": "文件路径"}}
3. run_shell: {{"command": "shell命令"}}

注意:
- 必须提供所有必需参数
- path必须以 /home/ubuntu/jarvis/ 开头（写入时）
- 如果不需要使用工具，可以返回空数组

请以JSON格式返回步骤列表:
[
    {{"tool": "工具名", "params": {{参数}}, "reason": "执行原因"}},
    ...
]
"""
                
                response = chat(prompt)
                
                # 输出思考过程
                emit("assistant", f"### 阶段 {phase.id}: {phase.title}\n\n{response}\n")
                
                # 解析步骤
                try:
                    import re
                    import json
                    
                    # 先尝试去除markdown代码块标记
                    cleaned_response = response
                    
                    # 删除```json ... ```或``` ... ```代码块
                    code_block_pattern = r'```(?:json)?\s*([\s\S]*?)```'
                    code_block_match = re.search(code_block_pattern, response)
                    if code_block_match:
                        cleaned_response = code_block_match.group(1)
                    
                    # 提取JSON数组
                    json_match = re.search(r'\[[\s\S]*\]', cleaned_response)
                    if json_match:
                        json_str = json_match.group(0)
                        steps = json.loads(json_str)
                        
                        # 验证是否为列表
                        if not isinstance(steps, list):
                            steps = []
                    else:
                        steps = []
                except Exception as e:
                    emit("error", f"⚠️ JSON解析失败: {str(e)}")
                    steps = []
                
                # 执行步骤
                for step in steps:
                    tool = step.get("tool")
                    params = step.get("params", {})
                    reason = step.get("reason", "")
                    
                    if tool and params:
                        emit("status", f"🛠️ 执行: {reason}")
                        
                        # 记录工具使用
                        self.current_task_tools_used.append(tool)
                        
                        # 添加到知识图谱
                        tool_id = f"tool_{tool}"
                        if not self.knowledge_graph.get_entity(tool_id):
                            self.knowledge_graph.add_entity(tool_id, "tool", {"name": tool})
                        self.knowledge_graph.add_relation(
                            self.current_task_id,
                            "uses",
                            tool_id
                        )
                        
                        # 执行工具（使用韧性引擎）
                        emit("status", f"🛠️ 执行: {reason}")
                        success, result = self.resilience.execute_with_resilience(
                            tool=tool,
                            params=params,
                            reason=reason,
                            emit=emit
                        )
                        
                        if success:
                            emit("status", f"✅ 完成: {tool}")
                        else:
                            error = result.get("error", "未知错误")
                            emit("error", f"❌ 失败: {tool} - {error}")
                            
                            # 记录错误到日志系统
                            self.error_logger.log_error(
                                error_type="tool_execution_error",
                                error_msg=error,
                                task_id=self.current_task_id,
                                phase_id=phase.id,
                                phase_title=phase.title,
                                tool_name=tool,
                                context={"params": params, "reason": reason}
                            )
                            
                            phase.mark_failed(error)
                            return False
                
                # 阶段成功
                phase.mark_completed(f"已完成 {len(steps)} 个步骤")
                return True
            
            else:
                # 纯思考阶段
                prompt = f"""
你是JARVIS，正在执行任务的一个阶段。

**任务目标**: {goal}
**当前阶段**: {phase.title}
**阶段描述**: {phase.description}

请详细阐述你的思考过程和分析结果。
"""
                
                response = chat(prompt)
                
                # 输出思考过程
                emit("assistant", f"### 阶段 {phase.id}: {phase.title}\n\n{response}\n")
                
                # 阶段成功
                phase.mark_completed("思考完成")
                return True
        
        except Exception as e:
            phase.mark_failed(str(e))
            return False
    
    def _record_task_completion(
        self,
        success: bool,
        iterations: int,
        error_msg: str = None
    ) -> None:
        """记录任务完成情况"""
        duration = time.time() - self.current_task_start_time
        goal = self.current_plan.goal if self.current_plan else "unknown"
        
        # 1. 反馈学习
        self.learner.record_task_execution(
            task_id=self.current_task_id,
            goal=goal,
            strategy="structured_planning",
            success=success,
            duration=duration,
            iterations=iterations,
            error_msg=error_msg,
            user_satisfaction=None
        )
        
        # 2. 迁移学习
        if success:
            self.transfer_learner.extract_task_pattern(
                task_id=self.current_task_id,
                goal=goal,
                strategy="structured_planning",
                tools_used=self.current_task_tools_used,
                success=True,
                duration=duration,
                key_steps=[p.title for p in self.current_plan.phases] if self.current_plan else []
            )
        
        # 3. 进化循环
        error_type = None
        if error_msg:
            if "file" in error_msg.lower():
                error_type = "file_error"
            elif "permission" in error_msg.lower():
                error_type = "permission_error"
            elif "timeout" in error_msg.lower():
                error_type = "timeout"
            else:
                error_type = "unknown"
        
        self.evolution_loop.monitor_task(
            task_id=self.current_task_id,
            success=success,
            duration=duration,
            iterations=iterations,
            tools_used=self.current_task_tools_used,
            error_type=error_type
        )


# 全局实例
_agent = None

def get_agent() -> JarvisAgentFinal:
    """获取全局agent实例"""
    global _agent
    if _agent is None:
        _agent = JarvisAgentFinal()
    return _agent


if __name__ == "__main__":
    # 测试代码
    agent = JarvisAgentFinal()
    result = agent.run("创建一个Python脚本，打印Hello World")
    print(f"\n最终结果: {result}")
