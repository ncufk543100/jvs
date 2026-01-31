"""
Execution Profile（执行剖面）模块

核心理念：不是"绕过制度"，而是"受控的执行通道"
- 不跳过 Sovereignty，只替换评估策略
- 所有操作都有审计记录
- 虚拟环境降级为告警而不是跳过
- confidence < 1.0，明确标记 DEV PROFILE
- 不影响 Hard Boundaries
"""
from enum import Enum
from dataclasses import dataclass
from typing import Optional
import os


class ExecutionProfile(Enum):
    """执行剖面类型"""
    STRICT = "strict"          # 生产/默认模式：完整评估
    DEVELOPMENT = "dev"        # 开发模式：快速评估
    EXPERIMENT = "experiment"  # 实验模式：SREP实验


@dataclass
class ProfileContext:
    """执行剖面上下文"""
    profile: ExecutionProfile
    reason: str  # 为什么使用这个profile
    environment: str  # 环境标识（sandbox/dev/prod）
    
    def is_strict(self) -> bool:
        return self.profile == ExecutionProfile.STRICT
    
    def is_development(self) -> bool:
        return self.profile == ExecutionProfile.DEVELOPMENT
    
    def is_experiment(self) -> bool:
        return self.profile == ExecutionProfile.EXPERIMENT


def detect_environment() -> str:
    """检测当前运行环境"""
    # 检查环境变量
    if os.getenv("JARVIS_ENV") == "production":
        return "production"
    if os.getenv("JARVIS_ENV") == "sandbox":
        return "sandbox"
    if os.getenv("JARVIS_ENV") == "dev":
        return "dev"
    
    # 检查是否在容器中
    if os.path.exists("/.dockerenv"):
        return "sandbox"
    
    # 默认为开发环境
    return "dev"


def get_default_profile() -> ExecutionProfile:
    """根据环境获取默认profile"""
    env = detect_environment()
    
    if env == "production":
        return ExecutionProfile.STRICT
    elif env == "sandbox":
        return ExecutionProfile.DEVELOPMENT
    else:
        return ExecutionProfile.DEVELOPMENT


def create_profile_context(
    profile: Optional[ExecutionProfile] = None,
    reason: str = ""
) -> ProfileContext:
    """创建执行剖面上下文"""
    if profile is None:
        profile = get_default_profile()
    
    env = detect_environment()
    
    # 生产环境强制使用STRICT
    if env == "production" and profile != ExecutionProfile.STRICT:
        profile = ExecutionProfile.STRICT
        reason = "生产环境强制使用STRICT模式"
    
    if not reason:
        reason = f"默认{profile.value}模式"
    
    return ProfileContext(
        profile=profile,
        reason=reason,
        environment=env
    )


# 全局profile上下文（可以被覆盖）
_global_profile_context: Optional[ProfileContext] = None


def set_global_profile(profile: ExecutionProfile, reason: str = "") -> ProfileContext:
    """设置全局执行剖面"""
    global _global_profile_context
    _global_profile_context = create_profile_context(profile, reason)
    return _global_profile_context


def get_current_profile() -> ProfileContext:
    """获取当前执行剖面"""
    global _global_profile_context
    if _global_profile_context is None:
        _global_profile_context = create_profile_context()
    return _global_profile_context


def reset_profile():
    """重置为默认profile"""
    global _global_profile_context
    _global_profile_context = None
