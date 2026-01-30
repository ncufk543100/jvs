"""
韧性执行引擎 (Resilient Executor)
核心原则：失败不终止，反思和迭代直到成功
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
import time
import traceback
from autonomous_goal_generator import Goal
from capability_box import get_capability_box


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    output: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    attempts: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "execution_time": self.execution_time,
            "attempts": self.attempts
        }


@dataclass
class ExecutionContext:
    """执行上下文"""
    goals: List[Goal]
    current_goal: Optional[Goal] = None
    discovered_goals: List[Goal] = None
    state: Dict[str, Any] = None
    iteration: int = 0
    max_iterations: int = 10
    
    def __post_init__(self):
        if self.discovered_goals is None:
            self.discovered_goals = []
        if self.state is None:
            self.state = {}


class ResilientExecutor:
    """
    韧性执行器
    
    核心能力：
    1. 失败后不放弃，而是反思和重试
    2. 动态调整策略
    3. 在执行中发现新目标
    4. 持续优化直到满足标准
    """
    
    def __init__(self, capability_box=None):
        self.capability_box = capability_box if capability_box else get_capability_box()
        self.max_retries = 3
        self.escalation_threshold = 0.3
    
    def execute_with_evolution(self, goals: List[Goal], context: Dict[str, Any]) -> ExecutionResult:
        """
        韧性执行（带进化能力）
        
        这是核心方法：螺旋式迭代，持续改进
        """
        exec_context = ExecutionContext(
            goals=goals,
            state=context
        )
        
        start_time = time.time()
        total_attempts = 0
        
        while exec_context.iteration < exec_context.max_iterations:
            exec_context.iteration += 1
            
            # 选择当前目标
            if not exec_context.current_goal and exec_context.goals:
                exec_context.current_goal = exec_context.goals.pop(0)
            
            if not exec_context.current_goal:
                # 所有目标完成
                break
            
            try:
                # 1. 动态规划（基于历史经验）
                plan = self._generate_plan(exec_context.current_goal, exec_context)
                
                # 2. 执行并监控
                result = self._execute_step(plan, exec_context)
                total_attempts += 1
                
                # 3. 验证结果质量
                quality = self._evaluate_quality(result, exec_context.current_goal)
                
                if quality >= 0.8:
                    # 成功！记录并继续
                    exec_context.state["last_result"] = result
                    exec_context.current_goal = None  # 完成当前目标
                    continue
                
                # 4. 失败 → 进入反思模式
                diagnosis = self._diagnose_failure(result, exec_context)
                
                # 5. 策略进化
                if diagnosis["type"] == "recoverable":
                    # 可恢复错误：调整策略重试
                    exec_context.state.update(diagnosis.get("adjustments", {}))
                    continue
                
                elif diagnosis["type"] == "need_decomposition":
                    # 需要分解：将目标分解为子目标
                    subtasks = self._decompose_goal(exec_context.current_goal)
                    exec_context.goals = subtasks + exec_context.goals
                    exec_context.current_goal = None
                    continue
                
                elif diagnosis["type"] == "capability_gap":
                    # 能力缺口：尝试扩展能力
                    if self._try_extend_capability(diagnosis["missing_capability"]):
                        # 成功扩展，重试
                        continue
                    else:
                        # 无法扩展，跳过
                        exec_context.current_goal = None
                        continue
                
                else:
                    # 不可恢复错误：记录并跳过
                    exec_context.current_goal = None
                    continue
            
            except Exception as e:
                # 6. 异常捕获 → 知识萃取
                pattern = self._extract_failure_pattern(e, exec_context)
                self._store_failure_pattern(pattern)
                
                if exec_context.iteration < exec_context.max_iterations - 1:
                    # 切换到备用模式
                    exec_context.state["fallback_mode"] = True
                else:
                    # 最终失败
                    break
        
        execution_time = time.time() - start_time
        
        return ExecutionResult(
            success=len(exec_context.goals) == 0,
            output=exec_context.state.get("last_result"),
            execution_time=execution_time,
            attempts=total_attempts
        )
    
    def _generate_plan(self, goal: Goal, context: ExecutionContext) -> Dict[str, Any]:
        """生成执行计划"""
        # 简化版本：基于目标类型生成标准计划
        if goal.type == "task":
            return {
                "steps": [
                    {"action": "analyze", "target": goal.description},
                    {"action": "execute", "target": goal.description},
                    {"action": "verify", "target": goal.success_criteria}
                ]
            }
        elif goal.type == "improvement":
            return {
                "steps": [
                    {"action": "identify_issue", "target": goal.description},
                    {"action": "propose_fix", "target": goal.description},
                    {"action": "apply_fix", "target": goal.description},
                    {"action": "verify", "target": goal.success_criteria}
                ]
            }
        else:
            return {
                "steps": [
                    {"action": "execute", "target": goal.description}
                ]
            }
    
    def _execute_step(self, plan: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """执行步骤"""
        results = []
        
        for step in plan.get("steps", []):
            action = step.get("action")
            target = step.get("target")
            
            # 能力检查
            check_result = self.capability_box.check_action({
                "type": action,
                "target": target
            })
            
            if not check_result["allowed"]:
                results.append({
                    "step": action,
                    "success": False,
                    "error": check_result["reason"]
                })
                continue
            
            # 执行（简化版本）
            try:
                result = self._execute_action(action, target, context)
                results.append({
                    "step": action,
                    "success": True,
                    "result": result
                })
            except Exception as e:
                results.append({
                    "step": action,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "steps": results,
            "overall_success": all(r.get("success", False) for r in results)
        }
    
    def _execute_action(self, action: str, target: str, context: ExecutionContext) -> Any:
        """执行具体动作"""
        # 简化版本：实际应该调用具体的工具
        return f"执行 {action} on {target}"
    
    def _evaluate_quality(self, result: Dict[str, Any], goal: Goal) -> float:
        """评估结果质量"""
        if result.get("overall_success"):
            return 0.9
        else:
            return 0.3
    
    def _diagnose_failure(self, result: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """诊断失败原因"""
        # 简化版本：实际应该使用 LLM 进行深度分析
        failed_steps = [s for s in result.get("steps", []) if not s.get("success")]
        
        if not failed_steps:
            return {"type": "unknown"}
        
        first_failure = failed_steps[0]
        error = first_failure.get("error", "")
        
        if "不在允许" in error or "不允许" in error:
            return {
                "type": "capability_gap",
                "missing_capability": first_failure.get("step")
            }
        
        if "复杂" in error or "困难" in error:
            return {"type": "need_decomposition"}
        
        return {
            "type": "recoverable",
            "adjustments": {"retry_count": context.iteration}
        }
    
    def _decompose_goal(self, goal: Goal) -> List[Goal]:
        """分解目标为子目标"""
        # 简化版本
        return [
            Goal(
                type="task",
                description=f"{goal.description} - 第1步",
                reason="分解后的子任务",
                priority=goal.priority,
                success_criteria="子任务完成",
                estimated_effort="low"
            ),
            Goal(
                type="task",
                description=f"{goal.description} - 第2步",
                reason="分解后的子任务",
                priority=goal.priority,
                success_criteria="子任务完成",
                estimated_effort="low"
            )
        ]
    
    def _try_extend_capability(self, capability: str) -> bool:
        """尝试扩展能力"""
        # 简化版本：实际应该尝试安装工具或学习新技能
        return False
    
    def _extract_failure_pattern(self, error: Exception, context: ExecutionContext) -> Dict[str, Any]:
        """从失败中提取模式"""
        return {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": {
                "goal": context.current_goal.description if context.current_goal else None,
                "iteration": context.iteration
            },
            "traceback": traceback.format_exc()
        }
    
    def _store_failure_pattern(self, pattern: Dict[str, Any]):
        """存储失败模式"""
        # 简化版本：实际应该存储到记忆系统
        pass


# 全局单例
_executor = None

def get_executor() -> ResilientExecutor:
    """获取全局执行器实例"""
    global _executor
    if _executor is None:
        _executor = ResilientExecutor()
    return _executor
