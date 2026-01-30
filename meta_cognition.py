"""
元认知层 (Meta-Cognition Layer)
核心能力：自我怀疑、策略进化、能力边界评估
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class ConfidenceLevel(Enum):
    """置信度等级"""
    VERY_HIGH = "very_high"  # > 0.9
    HIGH = "high"  # 0.7-0.9
    MEDIUM = "medium"  # 0.4-0.7
    LOW = "low"  # 0.2-0.4
    VERY_LOW = "very_low"  # < 0.2


@dataclass
class MetaCognitiveState:
    """元认知状态"""
    confidence: float  # 当前置信度
    uncertainty_sources: List[str]  # 不确定性来源
    known_limitations: List[str]  # 已知限制
    alternative_strategies: List[Dict[str, Any]]  # 备选策略
    should_ask_user: bool  # 是否应该询问用户
    reasoning: str  # 推理过程
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "confidence": self.confidence,
            "confidence_level": self.get_confidence_level().value,
            "uncertainty_sources": self.uncertainty_sources,
            "known_limitations": self.known_limitations,
            "alternative_strategies": self.alternative_strategies,
            "should_ask_user": self.should_ask_user,
            "reasoning": self.reasoning
        }
    
    def get_confidence_level(self) -> ConfidenceLevel:
        """获取置信度等级"""
        if self.confidence > 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif self.confidence > 0.7:
            return ConfidenceLevel.HIGH
        elif self.confidence > 0.4:
            return ConfidenceLevel.MEDIUM
        elif self.confidence > 0.2:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW


class MetaCognition:
    """
    元认知层
    
    核心能力：
    1. 自我怀疑：评估自己的判断是否可靠
    2. 不确定性管理：识别和处理不确定性
    3. 策略进化：动态调整策略
    4. 能力边界评估：知道自己能做什么、不能做什么
    5. 反事实推理：思考"如果...会怎样"
    """
    
    def __init__(self):
        self.capability_boundaries = {
            "can_do": [
                "代码分析和优化",
                "文件读写操作",
                "命令执行",
                "文档生成",
                "测试编写"
            ],
            "cannot_do": [
                "访问外部网络（受限）",
                "修改系统配置",
                "删除关键文件",
                "执行危险命令"
            ],
            "uncertain": [
                "复杂算法设计",
                "大规模重构",
                "性能调优"
            ]
        }
    
    def evaluate_confidence(self, context: Dict[str, Any]) -> MetaCognitiveState:
        """
        评估当前状态的置信度
        
        这是元认知的核心：知道自己知道什么、不知道什么
        """
        task = context.get("task", "")
        history = context.get("history", [])
        current_plan = context.get("plan", {})
        
        # 1. 基础置信度
        base_confidence = 0.7
        
        # 2. 识别不确定性来源
        uncertainty_sources = self._identify_uncertainties(context)
        
        # 3. 评估能力匹配度
        capability_match = self._evaluate_capability_match(task)
        
        # 4. 历史成功率影响
        if history:
            success_rate = sum(1 for h in history if h.get("success")) / len(history)
            base_confidence = base_confidence * 0.7 + success_rate * 0.3
        
        # 5. 计算最终置信度
        final_confidence = base_confidence * capability_match
        
        # 调整不确定性
        final_confidence -= len(uncertainty_sources) * 0.1
        final_confidence = max(0.0, min(1.0, final_confidence))
        
        # 6. 生成备选策略
        alternatives = self._generate_alternatives(context, final_confidence)
        
        # 7. 决定是否询问用户
        should_ask = final_confidence < 0.3 or len(uncertainty_sources) > 3
        
        # 8. 推理过程
        reasoning = self._explain_reasoning(
            final_confidence, 
            uncertainty_sources, 
            capability_match
        )
        
        return MetaCognitiveState(
            confidence=final_confidence,
            uncertainty_sources=uncertainty_sources,
            known_limitations=self.capability_boundaries["cannot_do"],
            alternative_strategies=alternatives,
            should_ask_user=should_ask,
            reasoning=reasoning
        )
    
    def _identify_uncertainties(self, context: Dict[str, Any]) -> List[str]:
        """识别不确定性来源"""
        uncertainties = []
        
        task = context.get("task", "")
        
        # 任务描述模糊
        if len(task) < 20:
            uncertainties.append("任务描述过于简短")
        
        # 包含不确定性词汇
        uncertain_words = ["可能", "也许", "大概", "不确定", "试试"]
        if any(word in task for word in uncertain_words):
            uncertainties.append("任务描述包含不确定性词汇")
        
        # 缺少成功标准
        if not context.get("success_criteria"):
            uncertainties.append("缺少明确的成功标准")
        
        # 涉及未知领域
        if any(domain in task for domain in ["区块链", "量子计算", "生物信息"]):
            uncertainties.append("涉及不熟悉的领域")
        
        return uncertainties
    
    def _evaluate_capability_match(self, task: str) -> float:
        """评估能力匹配度"""
        score = 0.5  # 基准分
        
        # 检查是否在能力范围内
        for capability in self.capability_boundaries["can_do"]:
            if any(keyword in task for keyword in capability.split()):
                score += 0.1
        
        # 检查是否超出能力
        for limitation in self.capability_boundaries["cannot_do"]:
            if any(keyword in task for keyword in limitation.split()):
                score -= 0.3
        
        return max(0.0, min(1.0, score))
    
    def _generate_alternatives(self, context: Dict[str, Any], confidence: float) -> List[Dict[str, Any]]:
        """生成备选策略"""
        alternatives = []
        
        if confidence < 0.5:
            # 低置信度：提供保守策略
            alternatives.append({
                "name": "conservative_approach",
                "description": "采用保守策略，分步验证",
                "confidence": 0.7,
                "steps": [
                    "先进行小范围测试",
                    "验证每一步结果",
                    "逐步扩大范围"
                ]
            })
            
            alternatives.append({
                "name": "ask_for_clarification",
                "description": "向用户询问更多信息",
                "confidence": 0.8,
                "steps": [
                    "列出不确定的点",
                    "请求用户澄清",
                    "基于反馈重新规划"
                ]
            })
        
        if confidence >= 0.5:
            # 中等置信度：提供标准策略
            alternatives.append({
                "name": "standard_approach",
                "description": "采用标准流程",
                "confidence": 0.8,
                "steps": [
                    "分析需求",
                    "制定计划",
                    "执行并验证"
                ]
            })
        
        return alternatives
    
    def _explain_reasoning(self, confidence: float, uncertainties: List[str], capability_match: float) -> str:
        """解释推理过程"""
        reasoning = f"置信度评估: {confidence:.2f}\n"
        reasoning += f"能力匹配度: {capability_match:.2f}\n"
        
        if uncertainties:
            reasoning += f"发现 {len(uncertainties)} 个不确定性:\n"
            for u in uncertainties:
                reasoning += f"  - {u}\n"
        
        if confidence > 0.7:
            reasoning += "结论: 有较高把握完成任务"
        elif confidence > 0.4:
            reasoning += "结论: 可以尝试，但需要谨慎"
        else:
            reasoning += "结论: 建议询问用户或采用保守策略"
        
        return reasoning
    
    def should_reconsider(self, execution_context: Dict[str, Any]) -> bool:
        """
        判断是否应该重新考虑当前策略
        
        触发条件：
        1. 连续失败多次
        2. 发现更好的方案
        3. 环境发生重大变化
        """
        failures = execution_context.get("consecutive_failures", 0)
        if failures >= 3:
            return True
        
        # 发现新信息
        if execution_context.get("new_information_discovered"):
            return True
        
        # 当前策略效果不佳
        if execution_context.get("current_strategy_score", 1.0) < 0.3:
            return True
        
        return False
    
    def counterfactual_reasoning(self, situation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        反事实推理："如果...会怎样"
        
        用于探索替代方案和预测结果
        """
        scenarios = []
        
        current_action = situation.get("action")
        
        # 场景1: 如果采用不同的方法
        scenarios.append({
            "hypothesis": f"如果不用{current_action}，而是用渐进式方法",
            "predicted_outcome": "可能更稳定但速度较慢",
            "confidence": 0.7
        })
        
        # 场景2: 如果寻求帮助
        scenarios.append({
            "hypothesis": "如果向用户询问更多细节",
            "predicted_outcome": "可以提高成功率，但增加交互成本",
            "confidence": 0.8
        })
        
        # 场景3: 如果分解任务
        scenarios.append({
            "hypothesis": "如果将任务分解为更小的子任务",
            "predicted_outcome": "更容易控制，但可能遗漏整体视角",
            "confidence": 0.75
        })
        
        return scenarios
    
    def detect_emergent_opportunities(self, execution_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        检测新兴机会
        
        在执行过程中发现原计划未覆盖的价值点
        """
        opportunities = []
        
        result = execution_result.get("result", {})
        
        # 检测可复用模式
        if self._has_reusable_pattern(result):
            opportunities.append({
                "type": "reusable_component",
                "description": "发现可提取为通用组件的模式",
                "value": "high",
                "effort": "medium"
            })
        
        # 检测性能优化机会
        if self._has_performance_opportunity(result):
            opportunities.append({
                "type": "performance_optimization",
                "description": "发现可以优化性能的地方",
                "value": "medium",
                "effort": "low"
            })
        
        # 检测扩展可能
        if self._has_extension_potential(result):
            opportunities.append({
                "type": "feature_extension",
                "description": "发现可以扩展的功能点",
                "value": "high",
                "effort": "high"
            })
        
        return opportunities
    
    def _has_reusable_pattern(self, result: Dict[str, Any]) -> bool:
        """检测可复用模式"""
        # 简化版本
        return False
    
    def _has_performance_opportunity(self, result: Dict[str, Any]) -> bool:
        """检测性能优化机会"""
        # 简化版本
        return False
    
    def _has_extension_potential(self, result: Dict[str, Any]) -> bool:
        """检测扩展潜力"""
        # 简化版本
        return False


# 全局单例
_meta_cognition = None

def get_meta_cognition() -> MetaCognition:
    """获取全局元认知实例"""
    global _meta_cognition
    if _meta_cognition is None:
        _meta_cognition = MetaCognition()
    return _meta_cognition
