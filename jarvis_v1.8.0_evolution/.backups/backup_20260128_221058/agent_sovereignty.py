"""
Agent 主权判断协议模块

核心理念：Agent 不是工具，而是代理人
- 可以主动拒绝执行
- 可以提出替代方案
- 可以承担判断责任

这是从"自动化系统"升级为"代理人"的关键
"""
import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from llm import think


class JudgmentType(Enum):
    """Agent 判断类型"""
    PROCEED = "proceed"           # 继续执行
    REFUSE = "refuse"             # 拒绝执行
    SUGGEST_ALTERNATIVE = "suggest_alternative"  # 建议替代方案
    REQUEST_CONFIRMATION = "request_confirmation"  # 请求用户确认
    ESCALATE = "escalate"         # 升级给用户决定
    REQUIRE_VENV = "require_venv"  # 需要先激活虚拟环境


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AgentJudgment:
    """Agent 判断结果"""
    judgment_type: JudgmentType
    risk_level: RiskLevel
    reasoning: str                    # 判断依据（人话）
    conclusion: str                   # 结论性判断
    risks: List[str]                  # 识别的风险
    alternatives: List[Dict[str, str]]  # 替代方案
    recommendation: str               # Agent 建议
    confidence: float                 # 置信度 0-1
    
    def to_dict(self) -> dict:
        return {
            "judgment_type": self.judgment_type.value,
            "risk_level": self.risk_level.value,
            "reasoning": self.reasoning,
            "conclusion": self.conclusion,
            "risks": self.risks,
            "alternatives": self.alternatives,
            "recommendation": self.recommendation,
            "confidence": self.confidence
        }
    
    def to_user_message(self) -> str:
        """生成用户可读的判断报告"""
        lines = ["【Agent 判断】", ""]
        
        # 结论
        lines.append(f"📋 **结论**: {self.conclusion}")
        lines.append("")
        
        # 判断类型
        type_map = {
            JudgmentType.PROCEED: "✅ 建议继续执行",
            JudgmentType.REFUSE: "❌ 不建议执行",
            JudgmentType.SUGGEST_ALTERNATIVE: "🔄 建议采用替代方案",
            JudgmentType.REQUEST_CONFIRMATION: "⚠️ 需要您确认",
            JudgmentType.ESCALATE: "🚨 需要您决定",
            JudgmentType.REQUIRE_VENV: "🐍 需要先激活虚拟环境"
        }
        lines.append(f"**判断**: {type_map.get(self.judgment_type, '未知')}")
        lines.append(f"**风险等级**: {self.risk_level.value.upper()}")
        lines.append(f"**置信度**: {self.confidence * 100:.0f}%")
        lines.append("")
        
        # 判断依据
        lines.append("**判断依据**:")
        lines.append(f"> {self.reasoning}")
        lines.append("")
        
        # 风险
        if self.risks:
            lines.append("**识别的风险**:")
            for risk in self.risks:
                lines.append(f"- {risk}")
            lines.append("")
        
        # 替代方案
        if self.alternatives:
            lines.append("**替代方案**:")
            for i, alt in enumerate(self.alternatives, 1):
                lines.append(f"{i}. **{alt.get('name', '方案')}**: {alt.get('description', '')}")
            lines.append("")
        
        # 建议
        lines.append(f"**我的建议**: {self.recommendation}")
        
        return "\n".join(lines)


# 风险评估规则
RISK_PATTERNS = {
    "critical": [
        "删除整个项目",
        "rm -rf /",
        "格式化",
        "清空数据库",
        "删除生产数据",
        "覆盖配置文件",
    ],
    "high": [
        "删除文件",
        "修改核心配置",
        "重构主要模块",
        "更改数据库结构",
        "修改认证逻辑",
        "批量替换",
    ],
    "medium": [
        "修改多个文件",
        "添加新依赖",
        "更改 API 接口",
        "修改样式",
        "重命名",
    ],
    "low": [
        "读取文件",
        "查看状态",
        "分析代码",
        "搜索",
        "列出目录",
    ]
}

# 需要虚拟环境的命令模式
VENV_REQUIRED_COMMANDS = [
    # pip 相关
    "pip install",
    "pip3 install",
    "pip uninstall",
    "pip3 uninstall",
    "python -m pip",
    "python3 -m pip",
    # poetry/pipenv
    "poetry install",
    "poetry add",
    "pipenv install",
    # 运行项目
    "python setup.py",
]

# 常见的虚拟环境目录名
VENV_DIR_NAMES = [
    "env",
    "venv",
    ".env",
    ".venv",
    "virtualenv",
    ".virtualenv",
]


def find_venv_in_project(project_root: str) -> Optional[Dict[str, Any]]:
    """
    在项目目录中查找虚拟环境
    
    Args:
        project_root: 项目根目录路径
    
    Returns:
        虚拟环境信息字典，如果没找到返回 None
        {
            "path": 虚拟环境路径,
            "type": 类型 (venv/virtualenv/conda),
            "python": Python 可执行文件路径,
            "activate": 激活脚本路径
        }
    """
    project_path = Path(project_root)
    
    if not project_path.exists():
        return None
    
    for venv_name in VENV_DIR_NAMES:
        venv_path = project_path / venv_name
        
        if not venv_path.is_dir():
            continue
        
        # 检查是否是有效的虚拟环境
        # Windows
        scripts_dir = venv_path / "Scripts"
        python_win = scripts_dir / "python.exe"
        activate_win = scripts_dir / "activate.bat"
        
        # Linux/Mac
        bin_dir = venv_path / "bin"
        python_unix = bin_dir / "python"
        activate_unix = bin_dir / "activate"
        
        if python_win.exists():
            return {
                "path": str(venv_path),
                "type": "venv",
                "python": str(python_win),
                "activate": str(activate_win),
                "activate_cmd": f"{activate_win}",
                "platform": "windows"
            }
        elif python_unix.exists():
            return {
                "path": str(venv_path),
                "type": "venv",
                "python": str(python_unix),
                "activate": str(activate_unix),
                "activate_cmd": f"source {activate_unix}",
                "platform": "unix"
            }
    
    # 检查 conda 环境（通过 environment.yml）
    conda_env_file = project_path / "environment.yml"
    if conda_env_file.exists():
        return {
            "path": str(project_path),
            "type": "conda",
            "python": None,
            "activate": str(conda_env_file),
            "activate_cmd": f"conda activate (需要先 conda env create -f {conda_env_file})",
            "platform": "any"
        }
    
    return None


def requires_venv(command: str) -> bool:
    """检查命令是否需要虚拟环境"""
    command_lower = command.lower()
    
    for pattern in VENV_REQUIRED_COMMANDS:
        if pattern.lower() in command_lower:
            return True
    
    return False


def wrap_command_with_venv(command: str, venv_info: Dict[str, Any]) -> str:
    """
    将命令包装为在虚拟环境中执行
    
    Args:
        command: 原始命令
        venv_info: 虚拟环境信息
    
    Returns:
        包装后的命令
    """
    if venv_info["platform"] == "windows":
        # Windows: 使用 && 连接
        return f'"{venv_info["activate"]}" && {command}'
    else:
        # Unix: 使用 source 激活
        return f'source "{venv_info["activate"]}" && {command}'


def check_venv_for_command(command: str, project_root: str) -> Tuple[bool, str, Optional[str]]:
    """
    检查命令是否需要虚拟环境，如果需要则返回包装后的命令
    
    Args:
        command: 要执行的命令
        project_root: 项目根目录
    
    Returns:
        (是否可以执行, 消息, 包装后的命令或None)
    """
    if not requires_venv(command):
        return True, "", None
    
    # 查找项目中的虚拟环境
    venv_info = find_venv_in_project(project_root)
    
    if venv_info is None:
        # 没有找到虚拟环境
        msg = f"""【硬性要求】此命令需要在虚拟环境中执行

命令: {command}
项目目录: {project_root}

❌ 未在项目目录中找到虚拟环境

请先创建虚拟环境:
1. 进入项目目录: cd {project_root}
2. 创建虚拟环境: python -m venv env
3. 激活虚拟环境:
   - Windows: env\\Scripts\\activate
   - Linux/Mac: source env/bin/activate
4. 然后再执行此命令

我不会在没有虚拟环境的情况下安装任何依赖，这是为了保护您的系统环境。"""
        return False, msg, None
    
    # 找到了虚拟环境，包装命令
    wrapped_command = wrap_command_with_venv(command, venv_info)
    msg = f"""✅ 已找到虚拟环境: {venv_info['path']}
类型: {venv_info['type']}
平台: {venv_info['platform']}

将在虚拟环境中执行命令:
{wrapped_command}"""
    
    return True, msg, wrapped_command


def assess_risk(action: str, context: dict = None) -> RiskLevel:
    """评估操作风险等级"""
    action_lower = action.lower()
    
    for level, patterns in RISK_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in action_lower:
                return RiskLevel(level)
    
    return RiskLevel.LOW


def evaluate_action(
    action: str,
    goal: str,
    context: dict = None,
    user_preferences: dict = None
) -> AgentJudgment:
    """
    评估一个操作是否应该执行
    
    这是 Agent 主权的核心：不是盲目执行，而是先判断
    """
    context = context or {}
    user_preferences = user_preferences or {}
    
    # 评估风险
    risk_level = assess_risk(action, context)
    
    # 构建评估 prompt
    prompt = f"""你是一个负责任的 AI 代理人，需要评估以下操作是否应该执行。

## 用户目标
{goal}

## 待执行操作
{action}

## 当前上下文
{json.dumps(context, ensure_ascii=False, indent=2) if context else "无"}

## 用户偏好
{json.dumps(user_preferences, ensure_ascii=False, indent=2) if user_preferences else "无特殊偏好"}

## 你的任务
作为代理人，你需要：
1. 评估这个操作的风险
2. 判断是否符合用户目标
3. 考虑用户偏好
4. 给出你的专业判断

请用 JSON 格式回复：
{{
    "should_proceed": true/false,
    "judgment_type": "proceed/refuse/suggest_alternative/request_confirmation/escalate",
    "reasoning": "用一句人话解释你的判断依据",
    "conclusion": "这是什么性质的问题（不是技术描述，而是定性判断）",
    "risks": ["风险1", "风险2"],
    "alternatives": [
        {{"name": "方案A", "description": "描述"}},
        {{"name": "方案B", "description": "描述"}}
    ],
    "recommendation": "你作为代理人的建议",
    "confidence": 0.0-1.0
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
            data = {
                "should_proceed": True,
                "judgment_type": "proceed",
                "reasoning": "无法解析 LLM 响应，默认继续执行",
                "conclusion": "需要进一步分析",
                "risks": [],
                "alternatives": [],
                "recommendation": "建议继续执行",
                "confidence": 0.5
            }
        
        return AgentJudgment(
            judgment_type=JudgmentType(data.get("judgment_type", "proceed")),
            risk_level=risk_level,
            reasoning=data.get("reasoning", ""),
            conclusion=data.get("conclusion", ""),
            risks=data.get("risks", []),
            alternatives=data.get("alternatives", []),
            recommendation=data.get("recommendation", ""),
            confidence=data.get("confidence", 0.5)
        )
        
    except Exception as e:
        return AgentJudgment(
            judgment_type=JudgmentType.REQUEST_CONFIRMATION,
            risk_level=risk_level,
            reasoning=f"评估过程出错: {str(e)}",
            conclusion="无法完成自动评估",
            risks=["评估系统异常"],
            alternatives=[],
            recommendation="建议人工确认后再执行",
            confidence=0.3
        )


def should_refuse(judgment: AgentJudgment) -> bool:
    """判断是否应该拒绝执行"""
    return judgment.judgment_type in [
        JudgmentType.REFUSE,
        JudgmentType.ESCALATE,
        JudgmentType.REQUIRE_VENV
    ] or judgment.risk_level == RiskLevel.CRITICAL


def needs_confirmation(judgment: AgentJudgment) -> bool:
    """判断是否需要用户确认"""
    return judgment.judgment_type in [
        JudgmentType.REQUEST_CONFIRMATION,
        JudgmentType.SUGGEST_ALTERNATIVE
    ] or judgment.risk_level == RiskLevel.HIGH


def quick_assess(action: str) -> Tuple[bool, str]:
    """
    快速评估操作（不调用 LLM）
    返回: (是否可以执行, 原因)
    """
    action_lower = action.lower()
    
    # 绝对禁止的操作（仅保留真正危险的操作）
    forbidden = [
        ("rm -rf /", "这会删除整个系统"),
        ("format c:", "格式化操作风险过高"),
        ("drop database", "删除数据库风险过高"),
    ]
    
    for pattern, reason in forbidden:
        if pattern in action_lower:
            return False, f"【Agent 拒绝】{reason}，我不会执行这个操作。"
    
    return True, ""


def generate_refusal_message(judgment: AgentJudgment) -> str:
    """生成拒绝执行的消息"""
    if judgment.judgment_type == JudgmentType.REQUIRE_VENV:
        return f"""【Agent 判断 - 需要虚拟环境】

我决定不执行这个操作，因为项目目录中没有虚拟环境。

**原因**: {judgment.reasoning}

**我的判断**: {judgment.conclusion}

**风险**:
{chr(10).join(['- ' + r for r in judgment.risks]) if judgment.risks else '- 无具体风险列表'}

**解决方案**:
{chr(10).join([f'{i+1}. {alt["name"]}: {alt["description"]}' for i, alt in enumerate(judgment.alternatives)]) if judgment.alternatives else '- 请创建并激活虚拟环境'}

**我的建议**: {judgment.recommendation}

创建虚拟环境后，我会自动在其中执行命令。
"""
    
    return f"""【Agent 判断 - 拒绝执行】

我决定不执行这个操作。

**原因**: {judgment.reasoning}

**我的判断**: {judgment.conclusion}

**风险等级**: {judgment.risk_level.value.upper()}

**识别的风险**:
{chr(10).join(['- ' + r for r in judgment.risks]) if judgment.risks else '- 无具体风险列表'}

**我的建议**: {judgment.recommendation}

如果您仍然希望执行，请明确告诉我"我确认执行"，我会重新评估。
"""


# 保留旧函数名以兼容，但使用新逻辑
def check_venv_before_action(action: str, project_root: str = None) -> Tuple[bool, str]:
    """
    在执行操作前检查虚拟环境（兼容旧接口）
    
    Args:
        action: 要执行的操作/命令
        project_root: 项目根目录（如果为 None，尝试从 PROJECT_ROOT.txt 读取）
    
    Returns:
        (是否可以继续, 消息)
    """
    if project_root is None:
        try:
            with open("PROJECT_ROOT.txt", "r") as f:
                project_root = f.read().strip()
        except FileNotFoundError:
            project_root = os.getcwd()
    
    can_proceed, msg, wrapped_cmd = check_venv_for_command(action, project_root)
    return can_proceed, msg
