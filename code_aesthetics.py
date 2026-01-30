"""
代码审美判断模型 (Code Aesthetics Model)
核心能力：评估代码质量，不仅看功能，还看"美感"
"""

from typing import Dict, Any, List
from dataclasses import dataclass
import re


@dataclass
class AestheticScore:
    """审美评分"""
    overall: float  # 总分 0-1
    dimensions: Dict[str, float]  # 各维度评分
    strengths: List[str]  # 优点
    weaknesses: List[str]  # 缺点
    suggestions: List[str]  # 改进建议
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall": self.overall,
            "dimensions": self.dimensions,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "suggestions": self.suggestions
        }


class CodeAestheticsModel:
    """
    代码审美判断模型
    
    评估维度：
    1. 简洁性 (Simplicity)
    2. 可读性 (Readability)
    3. 一致性 (Consistency)
    4. 优雅性 (Elegance)
    5. 健壮性 (Robustness)
    6. 可维护性 (Maintainability)
    """
    
    def __init__(self):
        self.weights = {
            "simplicity": 0.20,
            "readability": 0.20,
            "consistency": 0.15,
            "elegance": 0.15,
            "robustness": 0.15,
            "maintainability": 0.15
        }
    
    def evaluate(self, code: str, context: Dict[str, Any] = None) -> AestheticScore:
        """
        评估代码审美
        
        返回多维度评分和改进建议
        """
        context = context or {}
        
        # 各维度评分
        dimensions = {
            "simplicity": self._evaluate_simplicity(code),
            "readability": self._evaluate_readability(code),
            "consistency": self._evaluate_consistency(code),
            "elegance": self._evaluate_elegance(code),
            "robustness": self._evaluate_robustness(code),
            "maintainability": self._evaluate_maintainability(code)
        }
        
        # 计算总分
        overall = sum(
            dimensions[dim] * self.weights[dim]
            for dim in dimensions
        )
        
        # 提取优缺点
        strengths, weaknesses = self._extract_strengths_weaknesses(dimensions)
        
        # 生成改进建议
        suggestions = self._generate_suggestions(dimensions, code)
        
        return AestheticScore(
            overall=overall,
            dimensions=dimensions,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions
        )
    
    def _evaluate_simplicity(self, code: str) -> float:
        """评估简洁性"""
        score = 1.0
        
        # 代码行数（越短越好，但不能太短）
        lines = [l for l in code.split("\n") if l.strip()]
        if len(lines) > 100:
            score -= 0.2
        elif len(lines) < 10:
            score -= 0.1
        
        # 嵌套深度（越浅越好）
        max_indent = max((len(l) - len(l.lstrip()) for l in lines), default=0)
        if max_indent > 16:  # 超过4层嵌套
            score -= 0.3
        elif max_indent > 12:  # 超过3层嵌套
            score -= 0.2
        
        # 函数长度（越短越好）
        functions = re.findall(r'def \w+.*?(?=\ndef |\Z)', code, re.DOTALL)
        if functions:
            avg_func_lines = sum(len(f.split("\n")) for f in functions) / len(functions)
            if avg_func_lines > 50:
                score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def _evaluate_readability(self, code: str) -> float:
        """评估可读性"""
        score = 1.0
        
        # 命名质量（有意义的命名）
        bad_names = re.findall(r'\b[a-z]\b|\bx\b|\by\b|\btemp\b|\bdata\b', code)
        if len(bad_names) > 5:
            score -= 0.3
        
        # 注释覆盖率
        lines = code.split("\n")
        comment_lines = [l for l in lines if l.strip().startswith("#")]
        if len(lines) > 20 and len(comment_lines) == 0:
            score -= 0.2
        
        # 空行使用（适当的空行提升可读性）
        empty_lines = [l for l in lines if not l.strip()]
        if len(lines) > 30 and len(empty_lines) < 3:
            score -= 0.1
        
        # 文档字符串
        if 'def ' in code and '"""' not in code and "'''" not in code:
            score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def _evaluate_consistency(self, code: str) -> float:
        """评估一致性"""
        score = 1.0
        
        # 命名风格一致性
        snake_case = len(re.findall(r'\b[a-z]+_[a-z]+\b', code))
        camelCase = len(re.findall(r'\b[a-z]+[A-Z][a-z]+\b', code))
        
        if snake_case > 0 and camelCase > 0:
            score -= 0.3  # 混用命名风格
        
        # 引号一致性
        single_quotes = code.count("'")
        double_quotes = code.count('"')
        if single_quotes > 0 and double_quotes > 0:
            if abs(single_quotes - double_quotes) < min(single_quotes, double_quotes):
                score -= 0.2  # 混用引号
        
        return max(0.0, min(1.0, score))
    
    def _evaluate_elegance(self, code: str) -> float:
        """评估优雅性"""
        score = 0.5  # 基准分
        
        # 使用列表推导式（优雅）
        if '[' in code and 'for' in code and 'in' in code:
            score += 0.2
        
        # 使用上下文管理器（优雅）
        if 'with ' in code:
            score += 0.1
        
        # 使用装饰器（优雅）
        if '@' in code:
            score += 0.1
        
        # 避免重复代码
        lines = [l.strip() for l in code.split("\n") if l.strip()]
        unique_lines = set(lines)
        if len(lines) > 10:
            repetition_rate = 1 - len(unique_lines) / len(lines)
            if repetition_rate > 0.3:
                score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def _evaluate_robustness(self, code: str) -> float:
        """评估健壮性"""
        score = 0.5  # 基准分
        
        # 错误处理
        if 'try:' in code and 'except' in code:
            score += 0.2
        elif 'if ' in code and ('is None' in code or '== None' in code):
            score += 0.1
        
        # 输入验证
        if 'assert ' in code or 'raise ' in code:
            score += 0.1
        
        # 类型提示
        if '->' in code or ': ' in code:
            score += 0.1
        
        # 危险操作（减分）
        if 'eval(' in code or 'exec(' in code:
            score -= 0.3
        
        return max(0.0, min(1.0, score))
    
    def _evaluate_maintainability(self, code: str) -> float:
        """评估可维护性"""
        score = 1.0
        
        # 函数复杂度（圈复杂度简化版）
        complexity_indicators = code.count('if ') + code.count('for ') + code.count('while ')
        if complexity_indicators > 10:
            score -= 0.3
        
        # 全局变量（减分）
        lines = code.split("\n")
        global_vars = [l for l in lines if l.strip() and not l.strip().startswith(('def ', 'class ', '#', 'import ', 'from '))]
        if len(global_vars) > 5:
            score -= 0.2
        
        # 模块化（加分）
        if 'class ' in code or code.count('def ') > 3:
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _extract_strengths_weaknesses(self, dimensions: Dict[str, float]) -> tuple:
        """提取优缺点"""
        strengths = []
        weaknesses = []
        
        for dim, score in dimensions.items():
            dim_name = {
                "simplicity": "简洁性",
                "readability": "可读性",
                "consistency": "一致性",
                "elegance": "优雅性",
                "robustness": "健壮性",
                "maintainability": "可维护性"
            }[dim]
            
            if score >= 0.8:
                strengths.append(f"{dim_name}优秀 ({score:.2f})")
            elif score < 0.5:
                weaknesses.append(f"{dim_name}需要改进 ({score:.2f})")
        
        return strengths, weaknesses
    
    def _generate_suggestions(self, dimensions: Dict[str, float], code: str) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        if dimensions["simplicity"] < 0.6:
            suggestions.append("简化代码结构，减少嵌套层次")
        
        if dimensions["readability"] < 0.6:
            suggestions.append("改进命名，添加注释和文档字符串")
        
        if dimensions["consistency"] < 0.6:
            suggestions.append("统一命名风格和代码格式")
        
        if dimensions["elegance"] < 0.6:
            suggestions.append("使用更 Pythonic 的写法（列表推导、上下文管理器等）")
        
        if dimensions["robustness"] < 0.6:
            suggestions.append("添加错误处理和输入验证")
        
        if dimensions["maintainability"] < 0.6:
            suggestions.append("降低函数复杂度，提升模块化程度")
        
        return suggestions


# 全局单例
_aesthetics_model = None

def get_aesthetics_model() -> CodeAestheticsModel:
    """获取全局审美模型实例"""
    global _aesthetics_model
    if _aesthetics_model is None:
        _aesthetics_model = CodeAestheticsModel()
    return _aesthetics_model
