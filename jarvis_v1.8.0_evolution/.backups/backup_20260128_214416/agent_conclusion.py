"""
Agent 结论性判断模块

核心理念：从"分析"升级到"定性"
- 不只是描述问题，而是给出判断
- 不只是列出事实，而是得出结论
- 像专家一样思考，像代理人一样表达

这是让 Agent 从"技术报告"升级为"专业判断"的关键
"""
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from llm import think


class ProblemNature(Enum):
    """问题性质分类"""
    BUG = "bug"                          # 代码缺陷
    DESIGN_FLAW = "design_flaw"          # 设计缺陷
    ARCHITECTURE_ISSUE = "architecture"   # 架构问题
    LOGIC_ERROR = "logic_error"          # 逻辑错误
    STATE_MACHINE_ERROR = "state_machine" # 状态机错误
    RACE_CONDITION = "race_condition"    # 竞态条件
    CONFIGURATION = "configuration"       # 配置问题
    DEPENDENCY = "dependency"            # 依赖问题
    PERFORMANCE = "performance"          # 性能问题
    SECURITY = "security"                # 安全问题
    UX_ISSUE = "ux_issue"               # 用户体验问题
    MISUNDERSTANDING = "misunderstanding" # 需求理解偏差
    NOT_A_BUG = "not_a_bug"             # 不是 bug


class FixApproach(Enum):
    """修复方式分类"""
    HOTFIX = "hotfix"                    # 热修复/补丁
    REFACTOR = "refactor"                # 重构
    REDESIGN = "redesign"                # 重新设计
    CONFIGURATION_CHANGE = "config"      # 配置修改
    DEPENDENCY_UPDATE = "dependency"     # 依赖更新
    ROLLBACK = "rollback"                # 回滚
    NO_ACTION = "no_action"              # 无需操作


@dataclass
class AgentConclusion:
    """Agent 结论性判断"""
    # 核心判断
    nature: ProblemNature               # 问题性质
    conclusion: str                     # 一句话结论
    
    # 深度分析
    root_cause: str                     # 根本原因
    wrong_understanding: str            # 错误理解
    correct_understanding: str          # 正确理解
    
    # 修复建议
    recommended_approach: FixApproach   # 推荐修复方式
    fix_description: str                # 修复描述
    before_state: str                   # 修复前状态
    after_state: str                    # 修复后状态
    
    # 影响评估
    impact_scope: str                   # 影响范围
    risk_of_fix: str                    # 修复风险
    
    # 产品意义
    product_meaning: str                # 产品/交互意义
    
    def to_dict(self) -> dict:
        return {
            "nature": self.nature.value,
            "conclusion": self.conclusion,
            "root_cause": self.root_cause,
            "wrong_understanding": self.wrong_understanding,
            "correct_understanding": self.correct_understanding,
            "recommended_approach": self.recommended_approach.value,
            "fix_description": self.fix_description,
            "before_state": self.before_state,
            "after_state": self.after_state,
            "impact_scope": self.impact_scope,
            "risk_of_fix": self.risk_of_fix,
            "product_meaning": self.product_meaning
        }
    
    def to_report(self) -> str:
        """生成 Manus 风格的结论报告"""
        lines = [
            "# 【Agent 结论性判断】",
            "",
            f"## 📋 结论",
            f"> {self.conclusion}",
            "",
            f"**问题性质**: {self._nature_to_chinese(self.nature)}",
            "",
            "---",
            "",
            "## 🔍 核心原则",
            "",
            "| 维度 | 内容 |",
            "|------|------|",
            f"| ❌ 错误理解 | {self.wrong_understanding} |",
            f"| ✅ 正确理解 | {self.correct_understanding} |",
            "",
            "---",
            "",
            "## 🔧 修复方案",
            "",
            f"**推荐方式**: {self._approach_to_chinese(self.recommended_approach)}",
            "",
            f"**修复描述**: {self.fix_description}",
            "",
            "### Before → After",
            "",
            "| 修复前 | 修复后 |",
            "|--------|--------|",
            f"| {self.before_state} | {self.after_state} |",
            "",
            "---",
            "",
            "## 📊 影响评估",
            "",
            f"- **影响范围**: {self.impact_scope}",
            f"- **修复风险**: {self.risk_of_fix}",
            "",
            "---",
            "",
            "## 💡 产品/交互意义",
            "",
            f"> {self.product_meaning}",
            "",
            "---",
            "",
            "## 🎯 根本原因",
            "",
            f"{self.root_cause}",
        ]
        return "\n".join(lines)
    
    def _nature_to_chinese(self, nature: ProblemNature) -> str:
        mapping = {
            ProblemNature.BUG: "代码缺陷",
            ProblemNature.DESIGN_FLAW: "设计缺陷",
            ProblemNature.ARCHITECTURE_ISSUE: "架构问题",
            ProblemNature.LOGIC_ERROR: "逻辑错误",
            ProblemNature.STATE_MACHINE_ERROR: "状态机错误",
            ProblemNature.RACE_CONDITION: "竞态条件",
            ProblemNature.CONFIGURATION: "配置问题",
            ProblemNature.DEPENDENCY: "依赖问题",
            ProblemNature.PERFORMANCE: "性能问题",
            ProblemNature.SECURITY: "安全问题",
            ProblemNature.UX_ISSUE: "用户体验问题",
            ProblemNature.MISUNDERSTANDING: "需求理解偏差",
            ProblemNature.NOT_A_BUG: "不是 Bug",
        }
        return mapping.get(nature, nature.value)
    
    def _approach_to_chinese(self, approach: FixApproach) -> str:
        mapping = {
            FixApproach.HOTFIX: "热修复/补丁",
            FixApproach.REFACTOR: "重构",
            FixApproach.REDESIGN: "重新设计",
            FixApproach.CONFIGURATION_CHANGE: "配置修改",
            FixApproach.DEPENDENCY_UPDATE: "依赖更新",
            FixApproach.ROLLBACK: "回滚",
            FixApproach.NO_ACTION: "无需操作",
        }
        return mapping.get(approach, approach.value)


def generate_conclusion(
    problem_description: str,
    analysis_data: Dict[str, Any],
    context: Dict[str, Any] = None
) -> AgentConclusion:
    """
    生成结论性判断
    
    这是 Agent 的核心能力：不只是分析，而是定性
    """
    context = context or {}
    
    prompt = f"""你是一个资深的技术专家和 AI 代理人。
你的任务是对以下问题给出**结论性判断**，而不只是技术分析。

## 问题描述
{problem_description}

## 分析数据
{json.dumps(analysis_data, ensure_ascii=False, indent=2)}

## 上下文
{json.dumps(context, ensure_ascii=False, indent=2) if context else "无"}

## 你的任务

请像一个负责任的代理人一样，给出你的专业判断。

关键要求：
1. **结论要定性**：不是"可能是XX"，而是"这是XX"
2. **区分错误理解和正确理解**：帮助用户建立正确认知
3. **给出明确的修复建议**：不是"可以考虑"，而是"应该这样做"
4. **说明产品意义**：这个问题/修复对用户体验意味着什么

请用 JSON 格式回复：
{{
    "nature": "bug/design_flaw/architecture/logic_error/state_machine/race_condition/configuration/dependency/performance/security/ux_issue/misunderstanding/not_a_bug",
    "conclusion": "一句话结论（定性判断，不是描述）",
    "root_cause": "根本原因分析",
    "wrong_understanding": "常见的错误理解是什么",
    "correct_understanding": "正确的理解应该是什么",
    "recommended_approach": "hotfix/refactor/redesign/config/dependency/rollback/no_action",
    "fix_description": "具体修复方案描述",
    "before_state": "修复前的状态（简短）",
    "after_state": "修复后的状态（简短）",
    "impact_scope": "影响范围",
    "risk_of_fix": "修复风险评估",
    "product_meaning": "这对产品/用户体验意味着什么"
}}
"""
    
    try:
        response = think(prompt)
        
        # 解析 JSON
        json_match = None
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            json_match = response[start:end].strip()
        elif "{" in response:
            start = response.find("{")
            end = response.rfind("}") + 1
            json_match = response[start:end]
        
        if json_match:
            data = json.loads(json_match)
        else:
            data = _default_conclusion()
        
        return AgentConclusion(
            nature=ProblemNature(data.get("nature", "bug")),
            conclusion=data.get("conclusion", "需要进一步分析"),
            root_cause=data.get("root_cause", "未能确定根本原因"),
            wrong_understanding=data.get("wrong_understanding", ""),
            correct_understanding=data.get("correct_understanding", ""),
            recommended_approach=FixApproach(data.get("recommended_approach", "hotfix")),
            fix_description=data.get("fix_description", ""),
            before_state=data.get("before_state", ""),
            after_state=data.get("after_state", ""),
            impact_scope=data.get("impact_scope", "待评估"),
            risk_of_fix=data.get("risk_of_fix", "待评估"),
            product_meaning=data.get("product_meaning", "")
        )
        
    except Exception as e:
        return AgentConclusion(
            nature=ProblemNature.BUG,
            conclusion=f"分析过程出错: {str(e)}",
            root_cause="无法完成自动分析",
            wrong_understanding="",
            correct_understanding="",
            recommended_approach=FixApproach.NO_ACTION,
            fix_description="建议人工分析",
            before_state="未知",
            after_state="未知",
            impact_scope="未知",
            risk_of_fix="未知",
            product_meaning="需要人工评估"
        )


def _default_conclusion() -> dict:
    return {
        "nature": "bug",
        "conclusion": "需要进一步分析才能得出结论",
        "root_cause": "未能自动确定根本原因",
        "wrong_understanding": "",
        "correct_understanding": "",
        "recommended_approach": "hotfix",
        "fix_description": "建议人工分析后确定修复方案",
        "before_state": "当前状态",
        "after_state": "期望状态",
        "impact_scope": "待评估",
        "risk_of_fix": "待评估",
        "product_meaning": "需要进一步评估"
    }


def quick_conclusion(
    problem_type: str,
    symptom: str,
    cause: str
) -> str:
    """
    快速生成结论性判断（不调用 LLM）
    用于简单场景的快速响应
    """
    templates = {
        "ui_bug": f"这不是一个 UI 渲染问题，而是{cause}导致的状态同步错误。",
        "logic_error": f"这是一个逻辑错误：{cause}。表现为{symptom}。",
        "config_issue": f"这是配置问题，不是代码 bug。{cause}。",
        "design_flaw": f"这不是 bug，而是设计缺陷。{cause}需要重新设计。",
        "race_condition": f"这是竞态条件导致的问题。{symptom}的根本原因是{cause}。",
    }
    
    return templates.get(problem_type, f"问题分析：{symptom}。原因：{cause}。")


# 预定义的结论模板
CONCLUSION_TEMPLATES = {
    "animation_ui_conflict": {
        "nature": ProblemNature.STATE_MACHINE_ERROR,
        "wrong_understanding": "动画播放时 UI 卡顿是性能问题",
        "correct_understanding": "动画和 UI 更新共享同一个状态机，导致帧竞争",
        "recommended_approach": FixApproach.REDESIGN,
    },
    "async_state_sync": {
        "nature": ProblemNature.RACE_CONDITION,
        "wrong_understanding": "数据没有正确更新",
        "correct_understanding": "异步操作完成时，状态已经被其他操作覆盖",
        "recommended_approach": FixApproach.REFACTOR,
    },
    "config_not_loaded": {
        "nature": ProblemNature.CONFIGURATION,
        "wrong_understanding": "代码有 bug",
        "correct_understanding": "配置文件路径或格式不正确",
        "recommended_approach": FixApproach.CONFIGURATION_CHANGE,
    }
}


def apply_template(template_name: str, custom_data: dict = None) -> AgentConclusion:
    """应用预定义模板生成结论"""
    if template_name not in CONCLUSION_TEMPLATES:
        raise ValueError(f"未知模板: {template_name}")
    
    template = CONCLUSION_TEMPLATES[template_name]
    custom_data = custom_data or {}
    
    return AgentConclusion(
        nature=template.get("nature", ProblemNature.BUG),
        conclusion=custom_data.get("conclusion", ""),
        root_cause=custom_data.get("root_cause", ""),
        wrong_understanding=template.get("wrong_understanding", ""),
        correct_understanding=template.get("correct_understanding", ""),
        recommended_approach=template.get("recommended_approach", FixApproach.HOTFIX),
        fix_description=custom_data.get("fix_description", ""),
        before_state=custom_data.get("before_state", ""),
        after_state=custom_data.get("after_state", ""),
        impact_scope=custom_data.get("impact_scope", ""),
        risk_of_fix=custom_data.get("risk_of_fix", ""),
        product_meaning=custom_data.get("product_meaning", "")
    )
