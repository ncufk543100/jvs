"""
JARVIS 智能代理模块 v2.0.0 - 强自主AI架构
核心特性：
- 能力沙盒系统：不限制思想，只限制手脚
- 自主目标生成：AI自主发现问题和生成目标
- 韧性执行循环：失败不终止，反思和迭代
- 三层记忆系统：情景、程序、语义记忆
- 意图推断引擎：支持"给代码不给任务"场景
- 代码审美判断：多维度质量评估
- 元认知层：自我怀疑、策略进化、反事实推理
"""

import json
import time
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

# 导入现有模块
from platform_compatibility import normalize_path, is_windows
from llm import think, chat
from executor import execute, get_available_tools_with_meta
from safe_io import safe_write_json, safe_read_json
from event_bus import emit

# 导入 v2.0 新架构组件
from capability_box import CapabilityBox
from autonomous_goal_generator import AutonomousGoalGenerator
from resilient_executor import ResilientExecutor
from memory_system import MemorySystem, EpisodicMemory
from intent_inference import IntentInferenceEngine
from code_aesthetics import CodeAestheticsModel
from meta_cognition import MetaCognition

# 文件路径
_ROOT = Path(__file__).parent.absolute()
STATE_FILE = normalize_path(_ROOT / "STATE.json")
EVENTS_FILE = normalize_path(_ROOT / "EVENTS.json")

# 配置
MAX_ITERATIONS = 50
MAX_RETRIES_PER_GOAL = 3


class JarvisAgentV2:
    """
    JARVIS 2.0 强自主AI代理
    
    核心能力：
    1. 从原始输入推断意图（支持"给代码不给任务"）
    2. 自主生成和发现目标
    3. 韧性执行（失败后反思和重试）
    4. 元认知评估（知道自己知道什么）
    5. 动态目标发现（执行中发现新价值）
    6. 长期记忆和学习
    """
    
    def __init__(self):
        self.version = "2.0.0"
        
        # 初始化核心组件
        self.capability_box = CapabilityBox()
        self.goal_generator = AutonomousGoalGenerator()
        self.executor = ResilientExecutor(self.capability_box)
        self.memory = MemorySystem()
        self.intent_engine = IntentInferenceEngine()
        self.aesthetics = CodeAestheticsModel()
        self.meta_cognition = MetaCognition()
        
        # 任务状态
        self.task_id = None
        self.current_goals = []
        self.completed_goals = []
        self.iteration = 0
    
    def run(self, user_input: str, max_iterations: int = MAX_ITERATIONS) -> Dict[str, Any]:
        """
        主执行入口
        
        完整流程：
        1. 输入理解
        2. 意图推断
        3. 自主目标生成
        4. 元认知评估
        5. 韧性执行循环
        6. 动态目标发现
        7. 记忆和学习
        8. 持续优化
        """
        self.task_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        emit("task_start", {
            "task_id": self.task_id,
            "input": user_input,
            "version": self.version,
            "timestamp": datetime.now().isoformat()
        })
        
        try:
            # ========== 第1步：输入理解 ==========
            emit("phase", {"phase": "input_understanding", "input": user_input})
            input_analysis = self._analyze_input(user_input)
            
            # ========== 第2步：意图推断 ==========
            emit("phase", {"phase": "intent_inference"})
            intents = self.intent_engine.infer_intent(user_input, input_analysis)
            emit("intents_inferred", {
                "intents": [i.to_dict() for i in intents],
                "count": len(intents)
            })
            
            # ========== 第3步：自主目标生成 ==========
            emit("phase", {"phase": "goal_generation"})
            self.current_goals = self.goal_generator.generate_goals({
                "input": user_input,
                "intents": intents,
                "analysis": input_analysis,
                "current_state": {},
                "history": []
            })
            emit("goals_generated", {
                "goals": [g.to_dict() for g in self.current_goals],
                "count": len(self.current_goals)
            })
            
            # ========== 第4步：元认知评估 ==========
            emit("phase", {"phase": "meta_cognitive_evaluation"})
            meta_state = self.meta_cognition.evaluate_confidence({
                "task": user_input,
                "goals": [g.to_dict() for g in self.current_goals],
                "history": []
            })
            emit("meta_cognition", meta_state.to_dict())
            
            # 如果置信度极低，询问用户
            if meta_state.should_ask_user:
                emit("ask_user", {
                    "reason": "置信度过低",
                    "uncertainties": meta_state.uncertainty_sources,
                    "alternatives": meta_state.alternative_strategies
                })
                # 这里应该等待用户响应，简化版本直接继续
            
            # ========== 第5步：韧性执行循环 ==========
            emit("phase", {"phase": "resilient_execution"})
            execution_results = []
            
            for goal in self.current_goals:
                if self.iteration >= max_iterations:
                    emit("max_iterations_reached", {"iteration": self.iteration})
                    break
                
                emit("goal_start", {
                    "goal": goal.to_dict(),
                    "iteration": self.iteration
                })
                
                # 执行单个目标（带韧性）
                result = self._execute_goal_with_resilience(goal, max_retries=MAX_RETRIES_PER_GOAL)
                execution_results.append(result)
                
                if result["success"]:
                    self.completed_goals.append(goal)
                    emit("goal_completed", {
                        "goal": goal.to_dict(),
                        "result": result
                    })
                else:
                    emit("goal_failed", {
                        "goal": goal.to_dict(),
                        "result": result
                    })
                
                self.iteration += 1
            
            # ========== 第6步：动态目标发现 ==========
            emit("phase", {"phase": "dynamic_goal_discovery"})
            new_goals = self._discover_emergent_goals(execution_results)
            
            if new_goals:
                emit("new_goals_discovered", {
                    "goals": [g.to_dict() for g in new_goals],
                    "count": len(new_goals)
                })
                
                # 执行新发现的目标
                for goal in new_goals:
                    if self.iteration >= max_iterations:
                        break
                    
                    result = self._execute_goal_with_resilience(goal, max_retries=MAX_RETRIES_PER_GOAL)
                    execution_results.append(result)
                    self.iteration += 1
            
            # ========== 第7步：记忆和学习 ==========
            emit("phase", {"phase": "memory_and_learning"})
            self._commit_to_memory(user_input, execution_results)
            
            # ========== 第8步：持续优化评估 ==========
            emit("phase", {"phase": "continuous_optimization"})
            should_continue = self._should_continue_optimizing(user_input, execution_results)
            
            if should_continue and self.iteration < max_iterations:
                emit("continue_optimizing", {"reason": "发现改进空间"})
                # 递归调用（简化版本不递归，避免无限循环）
                # return self.run(user_input, max_iterations)
            
            # ========== 最终结果 ==========
            elapsed = time.time() - start_time
            final_result = {
                "task_id": self.task_id,
                "success": len(self.completed_goals) > 0,
                "completed_goals": len(self.completed_goals),
                "total_goals": len(self.current_goals),
                "iterations": self.iteration,
                "elapsed_time": elapsed,
                "results": execution_results,
                "memory_stats": self.memory.get_memory_stats()
            }
            
            emit("task_complete", final_result)
            return final_result
            
        except Exception as e:
            emit("task_error", {"error": str(e)})
            return {
                "task_id": self.task_id,
                "success": False,
                "error": str(e)
            }
    
    def _analyze_input(self, user_input: str) -> Dict[str, Any]:
        """分析输入特征"""
        return {
            "length": len(user_input),
            "is_code": self._is_code(user_input),
            "is_file_path": "/" in user_input or "\\" in user_input,
            "is_vague": len(user_input) < 50,
            "platform": "Windows" if is_windows() else "Linux"
        }
    
    def _is_code(self, text: str) -> bool:
        """判断是否是代码"""
        code_indicators = ["def ", "class ", "import ", "function ", "const ", "{", "}"]
        return any(indicator in text for indicator in code_indicators)
    
    def _execute_goal_with_resilience(self, goal, max_retries: int = 3) -> Dict[str, Any]:
        """
        使用韧性执行器执行单个目标
        
        失败后自动反思和重试
        """
        emit("executing_goal", {"goal": goal.to_dict()})
        
        # 制定执行计划
        plan = self._create_execution_plan(goal)
        
        # 韧性执行
        result = self.executor.execute_with_evolution(
            goals=[goal],
            context={
                "plan": plan,
                "max_retries": max_retries
            }
        )
        
        return result.to_dict()
    
    def _create_execution_plan(self, goal) -> Dict[str, Any]:
        """为目标创建执行计划"""
        # 使用 LLM 生成计划
        prompt = f"""为以下目标制定执行计划：

目标：{goal.description}
优先级：{goal.priority}
类型：{goal.type}

可用工具：
{json.dumps(get_available_tools_with_meta(), ensure_ascii=False, indent=2)}

请返回 JSON 格式的执行计划：
{{
    "steps": [
        {{"action": "工具名", "params": {{}}, "description": "步骤说明"}}
    ],
    "success_criteria": "成功标准",
    "estimated_time": "预计时间"
}}
"""
        
        try:
            response = think(prompt)
            # 解析 JSON
            plan = self._parse_json_robust(response)
            return plan
        except Exception as e:
            emit("plan_creation_failed", {"error": str(e)})
            # 返回默认计划
            return {
                "steps": [
                    {"action": "scan_files", "params": {}, "description": "扫描项目文件"}
                ],
                "success_criteria": "完成基础分析",
                "estimated_time": "1分钟"
            }
    
    def _parse_json_robust(self, text: str) -> Dict[str, Any]:
        """鲁棒的 JSON 解析"""
        # 尝试直接解析
        try:
            return json.loads(text)
        except:
            pass
        
        # 尝试提取 JSON 块
        import re
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        
        # 返回空字典
        return {}
    
    def _discover_emergent_goals(self, execution_results: List[Dict]) -> List:
        """发现新兴目标"""
        # 使用元认知检测机会
        opportunities = []
        for result in execution_results:
            opps = self.meta_cognition.detect_emergent_opportunities(result)
            opportunities.extend(opps)
        
        # 将机会转换为目标
        new_goals = []
        for opp in opportunities:
            if opp.get("value") == "high":
                new_goal = self.goal_generator.create_goal_from_opportunity(opp)
                if new_goal:
                    new_goals.append(new_goal)
        
        return new_goals
    
    def _commit_to_memory(self, user_input: str, results: List[Dict]):
        """提交到记忆系统"""
        # 存储情景记忆
        episode = EpisodicMemory(
            task_id=self.task_id,
            timestamp=datetime.now().isoformat(),
            input=user_input,
            goals=[g.to_dict() for g in self.current_goals],
            actions=[],  # 简化
            result={"results": results},
            success=any(r.get("success") for r in results)
        )
        self.memory.store_episode(episode)
        
        emit("memory_committed", {
            "episode_id": self.task_id,
            "success": episode.success
        })
    
    def _should_continue_optimizing(self, user_input: str, results: List[Dict]) -> bool:
        """判断是否应该继续优化"""
        # 检查任务描述中是否有"持续"、"全面"等关键词
        continuous_keywords = ["持续", "全面", "完全", "超越", "直到"]
        if any(kw in user_input for kw in continuous_keywords):
            # 检查是否真正达到目标
            success_rate = sum(1 for r in results if r.get("success")) / len(results) if results else 0
            if success_rate < 0.9:
                return True
        
        return False


def run_agent(user_input: str) -> Dict[str, Any]:
    """便捷函数：运行 JARVIS 2.0"""
    agent = JarvisAgentV2()
    return agent.run(user_input)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
        result = run_agent(task)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("用法: python agent_v2.py <任务描述>")
