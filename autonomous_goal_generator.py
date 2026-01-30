"""
自主目标生成引擎 (Autonomous Goal Generator)
核心原则：AI 自主发现问题、生成目标，无需用户授权
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json


@dataclass
class Goal:
    """目标数据类"""
    type: str  # "task" | "improvement" | "exploration" | "self_extension"
    description: str
    reason: str
    priority: int  # 1-10
    success_criteria: str
    estimated_effort: str  # "low" | "medium" | "high"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "description": self.description,
            "reason": self.reason,
            "priority": self.priority,
            "success_criteria": self.success_criteria,
            "estimated_effort": self.estimated_effort
        }


class AutonomousGoalGenerator:
    """
    自主目标生成器
    
    能力：
    1. 从输入推断目标（正向推断）
    2. 从缺失信息推断目标（反向推断）
    3. 从能力缺口生成改进目标
    4. 从执行过程中发现新目标（动态目标）
    """
    
    def __init__(self):
        self.common_intents = [
            "optimize_performance",
            "fix_bug",
            "modernize",
            "add_feature",
            "improve_readability",
            "security_harden",
            "test_coverage",
            "refactor_architecture",
            "add_documentation",
            "setup_ci_cd"
        ]
    
    def generate_goals(self, context: Dict[str, Any]) -> List[Goal]:
        """
        自主生成目标（核心方法）
        
        context 包含：
        - input: 用户输入
        - analysis: 输入分析结果
        - current_state: 当前状态
        - history: 历史记录
        """
        goals = []
        
        # 1. 从输入推断目标（正向推断）
        input_goals = self._infer_from_input(context)
        goals.extend(input_goals)
        
        # 2. 从缺失信息推断目标（反向推断）
        absence_goals = self._infer_from_absence(context)
        goals.extend(absence_goals)
        
        # 3. 从能力缺口生成目标
        capability_goals = self._generate_capability_goals(context)
        goals.extend(capability_goals)
        
        # 4. 从当前状态发现改进目标
        improvement_goals = self._discover_improvements(context)
        goals.extend(improvement_goals)
        
        # 5. 排序和去重
        goals = self._prioritize_goals(goals)
        
        return goals
    
    def _infer_from_input(self, context: Dict[str, Any]) -> List[Goal]:
        """从输入推断目标（正向推断）"""
        goals = []
        user_input = context.get("input", "")
        
        # 检测关键词
        if "超越" in user_input or "surpass" in user_input.lower():
            goals.append(Goal(
                type="task",
                description="全面超越参照系统",
                reason="用户明确要求超越",
                priority=10,
                success_criteria="在功能和体验上全面超越",
                estimated_effort="high"
            ))
        
        if "优化" in user_input or "optimize" in user_input.lower():
            goals.append(Goal(
                type="improvement",
                description="优化系统性能和代码质量",
                reason="用户提到优化",
                priority=8,
                success_criteria="性能提升明显，代码质量改善",
                estimated_effort="medium"
            ))
        
        # 如果输入是代码，推断代码相关目标
        if self._is_code(user_input):
            goals.extend(self._infer_code_goals(user_input))
        
        return goals
    
    def _infer_from_absence(self, context: Dict[str, Any]) -> List[Goal]:
        """从缺失信息推断目标（反向推断）"""
        goals = []
        analysis = context.get("analysis", {})
        
        # 检测缺失的东西
        absences = self._detect_absences(context)
        
        if absences.get("no_tests"):
            goals.append(Goal(
                type="improvement",
                description="添加测试覆盖",
                reason="项目缺少测试",
                priority=7,
                success_criteria="测试覆盖率 > 80%",
                estimated_effort="medium"
            ))
        
        if absences.get("no_docs"):
            goals.append(Goal(
                type="improvement",
                description="完善文档",
                reason="项目缺少文档",
                priority=6,
                success_criteria="关键模块都有文档",
                estimated_effort="low"
            ))
        
        if absences.get("no_error_handling"):
            goals.append(Goal(
                type="improvement",
                description="增强错误处理",
                reason="代码缺少错误处理",
                priority=8,
                success_criteria="关键路径都有错误处理",
                estimated_effort="medium"
            ))
        
        return goals
    
    def _generate_capability_goals(self, context: Dict[str, Any]) -> List[Goal]:
        """从能力缺口生成目标"""
        goals = []
        
        # 检测需要但没有的能力
        needed_capabilities = context.get("needed_capabilities", [])
        
        for cap in needed_capabilities:
            goals.append(Goal(
                type="self_extension",
                description=f"获得 {cap} 能力",
                reason=f"当前任务需要但系统缺少",
                priority=9,
                success_criteria=f"成功集成 {cap} 功能",
                estimated_effort="medium"
            ))
        
        return goals
    
    def _discover_improvements(self, context: Dict[str, Any]) -> List[Goal]:
        """发现改进机会"""
        goals = []
        current_state = context.get("current_state", {})
        
        # 分析当前状态，发现可以改进的地方
        if current_state.get("code_quality", 0) < 0.7:
            goals.append(Goal(
                type="improvement",
                description="提升代码质量",
                reason="当前代码质量低于标准",
                priority=7,
                success_criteria="代码质量评分 > 0.8",
                estimated_effort="medium"
            ))
        
        if current_state.get("performance_score", 0) < 0.6:
            goals.append(Goal(
                type="improvement",
                description="优化性能",
                reason="当前性能不佳",
                priority=8,
                success_criteria="性能评分 > 0.8",
                estimated_effort="high"
            ))
        
        return goals
    
    def _detect_absences(self, context: Dict[str, Any]) -> Dict[str, bool]:
        """检测缺失的东西"""
        # 简化版本，实际应该更复杂
        return {
            "no_tests": True,  # 暂时假设缺少测试
            "no_docs": False,
            "no_error_handling": False,
            "no_logging": False,
            "no_config": False
        }
    
    def _is_code(self, text: str) -> bool:
        """判断是否是代码"""
        code_indicators = ["def ", "class ", "import ", "function ", "const ", "var "]
        return any(indicator in text for indicator in code_indicators)
    
    def _infer_code_goals(self, code: str) -> List[Goal]:
        """从代码推断目标"""
        goals = []
        
        # 简化版本
        goals.append(Goal(
            type="task",
            description="分析和优化代码",
            reason="用户提供了代码",
            priority=8,
            success_criteria="代码分析完成，提出改进建议",
            estimated_effort="medium"
        ))
        
        return goals
    
    def _prioritize_goals(self, goals: List[Goal]) -> List[Goal]:
        """对目标排序和去重"""
        # 去重
        seen = set()
        unique_goals = []
        for goal in goals:
            key = (goal.type, goal.description)
            if key not in seen:
                seen.add(key)
                unique_goals.append(goal)
        
        # 按优先级排序
        unique_goals.sort(key=lambda g: g.priority, reverse=True)
        
        return unique_goals
    
    def discover_emergent_goals(self, execution_context: Dict[str, Any]) -> List[Goal]:
        """
        在执行过程中发现新目标（动态目标发现）
        
        这是关键能力：执行中发现原计划未覆盖的价值点
        """
        goals = []
        
        # 从执行结果中发现机会
        result = execution_context.get("result", {})
        
        # 例：发现可以提取为通用库
        if self._detect_reusable_pattern(result):
            goals.append(Goal(
                type="exploration",
                description="提取通用库",
                reason="发现可复用的模式",
                priority=6,
                success_criteria="成功提取为独立模块",
                estimated_effort="medium"
            ))
        
        # 例：发现可以并行化
        if self._detect_parallelizable(result):
            goals.append(Goal(
                type="improvement",
                description="并行化处理",
                reason="发现可以并行的操作",
                priority=7,
                success_criteria="吞吐量提升 > 2x",
                estimated_effort="medium"
            ))
        
        return goals
    
    def _detect_reusable_pattern(self, result: Dict[str, Any]) -> bool:
        """检测可复用模式"""
        # 简化版本
        return False
    
    def _detect_parallelizable(self, result: Dict[str, Any]) -> bool:
        """检测可并行化的操作"""
        # 简化版本
        return False


# 全局单例
_goal_generator = None

def get_goal_generator() -> AutonomousGoalGenerator:
    """获取全局目标生成器实例"""
    global _goal_generator
    if _goal_generator is None:
        _goal_generator = AutonomousGoalGenerator()
    return _goal_generator
