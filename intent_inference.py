"""
意图推断引擎 (Intent Inference Engine)
核心能力：从原始输入推断用户意图，支持"给代码不给任务"场景
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import re


@dataclass
class Intent:
    """意图数据类"""
    name: str  # 意图名称
    confidence: float  # 置信度 0-1
    evidence: List[str]  # 支持证据
    inferred_goals: List[str]  # 推断出的目标
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "inferred_goals": self.inferred_goals
        }


class IntentInferenceEngine:
    """
    意图推断引擎
    
    策略：
    1. 正向推断：从存在的信息推断
    2. 反向推断：从缺失的信息推断
    3. 上下文推断：从历史和环境推断
    """
    
    def __init__(self):
        # 意图模板库
        self.intent_templates = {
            "code_review": {
                "indicators": ["review", "检查", "审查", "看看"],
                "goals": ["分析代码质量", "发现潜在问题", "提出改进建议"]
            },
            "code_fix": {
                "indicators": ["fix", "修复", "bug", "错误", "不工作"],
                "goals": ["定位错误", "修复问题", "验证修复"]
            },
            "code_optimize": {
                "indicators": ["optimize", "优化", "性能", "慢", "快"],
                "goals": ["分析性能瓶颈", "优化算法", "提升性能"]
            },
            "code_refactor": {
                "indicators": ["refactor", "重构", "改进", "整理"],
                "goals": ["改善代码结构", "提升可维护性", "消除技术债"]
            },
            "code_complete": {
                "indicators": ["complete", "完成", "实现", "TODO"],
                "goals": ["实现缺失功能", "补充实现", "完善代码"]
            },
            "code_test": {
                "indicators": ["test", "测试", "验证"],
                "goals": ["编写测试用例", "执行测试", "验证功能"]
            },
            "code_document": {
                "indicators": ["document", "文档", "注释", "说明"],
                "goals": ["添加文档", "完善注释", "编写README"]
            },
            "code_modernize": {
                "indicators": ["modernize", "现代化", "升级", "更新"],
                "goals": ["升级依赖", "采用新特性", "改进架构"]
            }
        }
    
    def infer_intent(self, raw_input: str, context: Dict[str, Any] = None) -> List[Intent]:
        """
        推断意图（核心方法）
        
        支持"给代码不给任务"场景
        """
        context = context or {}
        intents = []
        
        # 1. 分析输入类型
        input_analysis = self._analyze_input(raw_input)
        
        # 2. 正向推断（从存在的信息）
        positive_intents = self._infer_from_positive(raw_input, input_analysis)
        intents.extend(positive_intents)
        
        # 3. 反向推断（从缺失的信息）
        negative_intents = self._infer_from_negative(raw_input, input_analysis)
        intents.extend(negative_intents)
        
        # 4. 上下文推断（从历史和环境）
        contextual_intents = self._infer_from_context(raw_input, context)
        intents.extend(contextual_intents)
        
        # 5. 如果没有明确任务，推断默认意图
        if not intents and input_analysis["is_code"]:
            intents = self._infer_default_code_intents(raw_input, input_analysis)
        
        # 6. 排序和去重
        intents = self._rank_intents(intents)
        
        return intents
    
    def _analyze_input(self, raw_input: str) -> Dict[str, Any]:
        """分析输入特征"""
        analysis = {
            "is_code": self._is_code(raw_input),
            "is_file_path": self._is_file_path(raw_input),
            "is_question": self._is_question(raw_input),
            "is_command": self._is_command(raw_input),
            "language": self._detect_language(raw_input),
            "length": len(raw_input),
            "has_error_indicators": self._has_error_indicators(raw_input),
            "has_todo": "TODO" in raw_input or "FIXME" in raw_input,
            "has_test": "test" in raw_input.lower() or "assert" in raw_input.lower()
        }
        
        return analysis
    
    def _infer_from_positive(self, raw_input: str, analysis: Dict[str, Any]) -> List[Intent]:
        """正向推断：从存在的信息推断意图"""
        intents = []
        
        # 检查关键词匹配
        for intent_name, template in self.intent_templates.items():
            evidence = []
            for indicator in template["indicators"]:
                if indicator.lower() in raw_input.lower():
                    evidence.append(f"包含关键词: {indicator}")
            
            if evidence:
                intents.append(Intent(
                    name=intent_name,
                    confidence=0.7 + len(evidence) * 0.1,
                    evidence=evidence,
                    inferred_goals=template["goals"]
                ))
        
        return intents
    
    def _infer_from_negative(self, raw_input: str, analysis: Dict[str, Any]) -> List[Intent]:
        """反向推断：从缺失的信息推断意图"""
        intents = []
        
        if analysis["is_code"]:
            # 代码缺少测试
            if not analysis["has_test"]:
                intents.append(Intent(
                    name="code_test",
                    confidence=0.6,
                    evidence=["代码缺少测试"],
                    inferred_goals=["编写测试用例", "提升测试覆盖率"]
                ))
            
            # 代码有 TODO
            if analysis["has_todo"]:
                intents.append(Intent(
                    name="code_complete",
                    confidence=0.8,
                    evidence=["代码包含 TODO/FIXME"],
                    inferred_goals=["实现 TODO 标记的功能"]
                ))
            
            # 代码有错误迹象
            if analysis["has_error_indicators"]:
                intents.append(Intent(
                    name="code_fix",
                    confidence=0.7,
                    evidence=["代码可能有错误"],
                    inferred_goals=["定位和修复错误"]
                ))
        
        return intents
    
    def _infer_from_context(self, raw_input: str, context: Dict[str, Any]) -> List[Intent]:
        """上下文推断：从历史和环境推断意图"""
        intents = []
        
        # 从历史任务推断
        last_task = context.get("last_task")
        if last_task:
            # 如果上次是修复，这次可能是验证
            if "fix" in last_task.lower():
                intents.append(Intent(
                    name="code_test",
                    confidence=0.5,
                    evidence=["上次任务是修复，可能需要验证"],
                    inferred_goals=["验证修复效果"]
                ))
        
        return intents
    
    def _infer_default_code_intents(self, raw_input: str, analysis: Dict[str, Any]) -> List[Intent]:
        """
        推断默认代码意图
        
        当用户只给代码不给任务时，推断他可能想要什么
        """
        intents = []
        
        # 默认意图：全面分析和改进
        intents.append(Intent(
            name="comprehensive_analysis",
            confidence=0.9,
            evidence=["用户提供代码但未明确任务"],
            inferred_goals=[
                "分析代码质量",
                "发现潜在问题",
                "提出优化建议",
                "检查安全性",
                "评估性能",
                "建议测试策略"
            ]
        ))
        
        return intents
    
    def _is_code(self, text: str) -> bool:
        """判断是否是代码"""
        code_indicators = [
            "def ", "class ", "import ", "from ",
            "function ", "const ", "var ", "let ",
            "public ", "private ", "void ",
            "{", "}", "=>", "->",
            "if (", "for (", "while ("
        ]
        return any(indicator in text for indicator in code_indicators)
    
    def _is_file_path(self, text: str) -> bool:
        """判断是否是文件路径"""
        return "/" in text or "\\" in text or text.endswith((".py", ".js", ".java", ".cpp"))
    
    def _is_question(self, text: str) -> bool:
        """判断是否是问题"""
        return "?" in text or text.strip().endswith("？")
    
    def _is_command(self, text: str) -> bool:
        """判断是否是命令"""
        command_verbs = ["请", "帮我", "给我", "分析", "优化", "修复", "检查"]
        return any(verb in text for verb in command_verbs)
    
    def _detect_language(self, text: str) -> Optional[str]:
        """检测编程语言"""
        if "def " in text and "import " in text:
            return "python"
        elif "function " in text or "const " in text:
            return "javascript"
        elif "public class" in text:
            return "java"
        return None
    
    def _has_error_indicators(self, text: str) -> bool:
        """检测错误指示"""
        error_keywords = ["error", "错误", "exception", "异常", "bug", "fail", "失败"]
        return any(keyword in text.lower() for keyword in error_keywords)
    
    def _rank_intents(self, intents: List[Intent]) -> List[Intent]:
        """对意图排序和去重"""
        # 去重
        seen = set()
        unique_intents = []
        for intent in intents:
            if intent.name not in seen:
                seen.add(intent.name)
                unique_intents.append(intent)
        
        # 按置信度排序
        unique_intents.sort(key=lambda i: i.confidence, reverse=True)
        
        return unique_intents
    
    def generate_hypotheses(self, raw_input: str) -> List[Dict[str, Any]]:
        """
        生成假设（用于快速验证）
        
        返回多个可能的意图假设，供快速验证
        """
        intents = self.infer_intent(raw_input)
        
        hypotheses = []
        for intent in intents:
            hypotheses.append({
                "hypothesis": f"用户想要{intent.name}",
                "confidence": intent.confidence,
                "validation_steps": [
                    f"检查是否{goal}" for goal in intent.inferred_goals[:2]
                ],
                "expected_outcome": intent.inferred_goals[0] if intent.inferred_goals else "完成任务"
            })
        
        return hypotheses


# 全局单例
_intent_engine = None

def get_intent_engine() -> IntentInferenceEngine:
    """获取全局意图推断引擎实例"""
    global _intent_engine
    if _intent_engine is None:
        _intent_engine = IntentInferenceEngine()
    return _intent_engine
