"""
用户偏好系统模块

核心理念：Agent 应该越用越懂你
- 记住用户的偏好
- 根据偏好调整决策
- 像了解你的助手一样工作

这是让 Agent 建立"长期信任"的关键
"""
import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from safe_io import safe_write_json, safe_read_json


# 偏好文件路径
PREFERENCES_FILE = Path(__file__).parent / "USER_PREFERENCES.json"


@dataclass
class UserPreferences:
    """用户偏好配置"""
    
    # === 修复风格偏好 ===
    prefer_structural_fix: bool = True      # 偏好结构性修复（vs 热修复）
    avoid_hotfix: bool = False              # 避免热修复
    prefer_refactor: bool = False           # 偏好重构
    
    # === 代码风格偏好 ===
    code_style: str = "standard"            # 代码风格: standard/verbose/minimal
    prefer_comments: bool = True            # 偏好添加注释
    prefer_type_hints: bool = True          # 偏好类型提示
    
    # === 确认偏好 ===
    ui_changes_require_confirmation: bool = True    # UI 修改需要确认
    config_changes_require_confirmation: bool = True # 配置修改需要确认
    delete_requires_confirmation: bool = True       # 删除需要确认（强制）
    batch_operations_forbidden: bool = False        # 禁止批量操作（已解除）
    
    # === 风险偏好 ===
    risk_tolerance: str = "medium"          # 风险容忍度: low/medium/high
    auto_rollback_on_error: bool = True     # 出错时自动回滚
    
    # === 沟通偏好 ===
    verbose_explanations: bool = True       # 详细解释
    show_alternatives: bool = True          # 显示替代方案
    language: str = "zh"                    # 语言偏好
    
    # === 工作流偏好 ===
    auto_commit: bool = False               # 自动提交 Git
    auto_test: bool = True                  # 修改后自动测试
    preserve_formatting: bool = True        # 保留原有格式
    
    # === 学习到的偏好（动态） ===
    learned_preferences: Dict[str, Any] = field(default_factory=dict)
    
    # === 元数据 ===
    created_at: str = ""
    updated_at: str = ""
    preference_history: List[Dict] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()


def load_preferences() -> UserPreferences:
    """加载用户偏好"""
    data = safe_read_json(str(PREFERENCES_FILE), default={})
    
    if not data:
        # 首次使用，创建默认偏好
        prefs = UserPreferences()
        save_preferences(prefs)
        return prefs
    
    # 处理 learned_preferences 和 preference_history
    learned = data.pop("learned_preferences", {})
    history = data.pop("preference_history", [])
    
    prefs = UserPreferences(**{k: v for k, v in data.items() 
                               if k in UserPreferences.__dataclass_fields__})
    prefs.learned_preferences = learned
    prefs.preference_history = history
    
    return prefs


def save_preferences(prefs: UserPreferences) -> None:
    """保存用户偏好"""
    prefs.updated_at = datetime.now().isoformat()
    safe_write_json(str(PREFERENCES_FILE), asdict(prefs))


def update_preference(key: str, value: Any, reason: str = "") -> UserPreferences:
    """更新单个偏好"""
    prefs = load_preferences()
    
    if hasattr(prefs, key):
        old_value = getattr(prefs, key)
        setattr(prefs, key, value)
        
        # 记录变更历史
        prefs.preference_history.append({
            "key": key,
            "old_value": old_value,
            "new_value": value,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })
        
        # 只保留最近 100 条历史
        if len(prefs.preference_history) > 100:
            prefs.preference_history = prefs.preference_history[-100:]
        
        save_preferences(prefs)
    
    return prefs


def learn_preference(key: str, value: Any, confidence: float = 0.5) -> None:
    """
    学习用户偏好（从用户行为中推断）
    
    这是 Agent 变得"越来越懂你"的关键
    """
    prefs = load_preferences()
    
    if key not in prefs.learned_preferences:
        prefs.learned_preferences[key] = {
            "value": value,
            "confidence": confidence,
            "observations": 1,
            "first_observed": datetime.now().isoformat(),
            "last_observed": datetime.now().isoformat()
        }
    else:
        # 更新已有偏好
        existing = prefs.learned_preferences[key]
        existing["observations"] += 1
        existing["last_observed"] = datetime.now().isoformat()
        
        # 如果新观察与已有值一致，增加置信度
        if existing["value"] == value:
            existing["confidence"] = min(1.0, existing["confidence"] + 0.1)
        else:
            # 如果不一致，降低置信度或更新值
            existing["confidence"] -= 0.1
            if existing["confidence"] < 0.3:
                existing["value"] = value
                existing["confidence"] = 0.5
    
    save_preferences(prefs)


def get_preference(key: str, default: Any = None) -> Any:
    """获取偏好值（包括学习到的偏好）"""
    prefs = load_preferences()
    
    # 先检查显式偏好
    if hasattr(prefs, key):
        return getattr(prefs, key)
    
    # 再检查学习到的偏好
    if key in prefs.learned_preferences:
        learned = prefs.learned_preferences[key]
        if learned["confidence"] >= 0.6:  # 只有置信度足够高才使用
            return learned["value"]
    
    return default


def should_confirm(action_type: str) -> bool:
    """根据偏好判断是否需要确认"""
    prefs = load_preferences()
    
    # 强制确认的操作
    if action_type == "delete":
        return True  # 删除始终需要确认
    
    if action_type == "batch":
        return prefs.batch_operations_forbidden  # 根据配置决定是否禁止批量操作
    
    # 根据偏好判断
    if action_type == "ui_change":
        return prefs.ui_changes_require_confirmation
    
    if action_type == "config_change":
        return prefs.config_changes_require_confirmation
    
    # 根据风险容忍度判断
    if prefs.risk_tolerance == "low":
        return True  # 低风险容忍度，所有操作都确认
    
    return False


def get_fix_preference() -> str:
    """获取修复风格偏好"""
    prefs = load_preferences()
    
    if prefs.avoid_hotfix:
        return "structural"
    if prefs.prefer_refactor:
        return "refactor"
    if prefs.prefer_structural_fix:
        return "structural"
    
    return "balanced"


def apply_preferences_to_decision(decision: Dict[str, Any]) -> Dict[str, Any]:
    """
    将用户偏好应用到决策中
    
    这是让偏好真正影响 Agent 行为的关键
    """
    prefs = load_preferences()
    
    # 添加偏好约束
    decision["preferences_applied"] = []
    
    # 检查是否需要确认
    action_type = decision.get("action_type", "")
    if should_confirm(action_type):
        decision["requires_confirmation"] = True
        decision["preferences_applied"].append(f"根据偏好，{action_type} 操作需要确认")
    
    # 检查修复风格
    if "fix_approach" in decision:
        preferred = get_fix_preference()
        if preferred == "structural" and decision["fix_approach"] == "hotfix":
            decision["preference_conflict"] = True
            decision["preferences_applied"].append("您偏好结构性修复，但当前方案是热修复")
    
    # 检查风险
    if decision.get("risk_level") == "high" and prefs.risk_tolerance == "low":
        decision["preference_conflict"] = True
        decision["preferences_applied"].append("此操作风险较高，但您的风险容忍度设置为低")
    
    # 添加偏好上下文
    decision["user_preferences_context"] = {
        "risk_tolerance": prefs.risk_tolerance,
        "prefer_structural_fix": prefs.prefer_structural_fix,
        "verbose_explanations": prefs.verbose_explanations,
    }
    
    return decision


def get_preferences_summary() -> str:
    """获取偏好摘要（用于 Agent 决策时参考）"""
    prefs = load_preferences()
    
    lines = [
        "## 用户偏好摘要",
        "",
        "### 修复风格",
        f"- 偏好结构性修复: {'是' if prefs.prefer_structural_fix else '否'}",
        f"- 避免热修复: {'是' if prefs.avoid_hotfix else '否'}",
        f"- 偏好重构: {'是' if prefs.prefer_refactor else '否'}",
        "",
        "### 确认要求",
        f"- UI 修改需确认: {'是' if prefs.ui_changes_require_confirmation else '否'}",
        f"- 配置修改需确认: {'是' if prefs.config_changes_require_confirmation else '否'}",
        f"- 删除需确认: 是（强制）",
        f"- 禁止批量操作: {'是' if prefs.batch_operations_forbidden else '否'}",
        "",
        "### 风险偏好",
        f"- 风险容忍度: {prefs.risk_tolerance}",
        f"- 出错自动回滚: {'是' if prefs.auto_rollback_on_error else '否'}",
        "",
    ]
    
    # 添加学习到的偏好
    if prefs.learned_preferences:
        lines.append("### 学习到的偏好")
        for key, data in prefs.learned_preferences.items():
            if data["confidence"] >= 0.6:
                lines.append(f"- {key}: {data['value']} (置信度: {data['confidence']:.0%})")
    
    return "\n".join(lines)


# 偏好推断规则
INFERENCE_RULES = {
    "user_rejected_hotfix": {
        "key": "avoid_hotfix",
        "value": True,
        "confidence_boost": 0.2
    },
    "user_asked_for_refactor": {
        "key": "prefer_refactor", 
        "value": True,
        "confidence_boost": 0.3
    },
    "user_requested_detailed_explanation": {
        "key": "verbose_explanations",
        "value": True,
        "confidence_boost": 0.2
    },
    "user_skipped_confirmation": {
        "key": "ui_changes_require_confirmation",
        "value": False,
        "confidence_boost": 0.1
    }
}


def infer_preference_from_action(action: str, user_response: str) -> None:
    """
    从用户行为推断偏好
    
    这是让 Agent "越用越懂你" 的核心机制
    """
    action_lower = action.lower()
    response_lower = user_response.lower()
    
    # 检查是否拒绝了热修复
    if "hotfix" in action_lower and ("不" in response_lower or "重构" in response_lower):
        learn_preference("avoid_hotfix", True, 0.7)
    
    # 检查是否要求详细解释
    if "详细" in response_lower or "解释" in response_lower or "为什么" in response_lower:
        learn_preference("verbose_explanations", True, 0.6)
    
    # 检查是否偏好结构性修复
    if "结构" in response_lower or "根本" in response_lower:
        learn_preference("prefer_structural_fix", True, 0.7)


def reset_preferences() -> UserPreferences:
    """重置为默认偏好"""
    prefs = UserPreferences()
    save_preferences(prefs)
    return prefs
