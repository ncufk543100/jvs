"""
JARVIS 执行器模块 (v1.7.1) - 工具觉醒版
核心特性：
- 工具元认知 (Tool Meta-Cognition)：每个工具都有详细的适用场景、风险和跨平台说明
- 自主工具创建：支持动态扩展工具箱
- 跨平台兼容性：Linux & Windows 11
"""
import json
import os
import glob
import datetime
import subprocess
import re
import importlib
from pathlib import Path
from sandbox import assert_in_sandbox
from safe_io import safe_write, safe_write_json
from agent_sovereignty import check_venv_for_command
from platform_compatibility import is_windows, normalize_path, get_shell_cmd, run_cross_platform_cmd
from skill_manager import manager as skill_manager

# 尝试导入自我修改模块
try:
    from self_modify import get_or_create_session, clear_session, request_restart
    SELF_MODIFY_AVAILABLE = True
except ImportError:
    SELF_MODIFY_AVAILABLE = False

STATE_FILE = "STATE.json"
SCAN_RULES = json.load(open("SCAN_RULES.json", encoding="utf-8"))

# Shell 命令白名单
ALLOWED_COMMANDS = [
    "ls", "dir", "cat", "type", "head", "tail", "wc", "grep", "findstr", "find", "echo",
    "pwd", "cd", "mkdir", "cp", "copy", "mv", "move", "rm", "del", "rd",
    "python", "python3", "pip", "pip3", "node", "npm", "git"
]

def load_state():
    return json.load(open(STATE_FILE, encoding="utf-8"))

def save_state(state):
    safe_write_json(STATE_FILE, state)

# ==================== 核心工具函数 ====================

def scan_files(params=None):
    root = normalize_path(params.get("path", ".")) if params else "."
    files = []
    for pattern in SCAN_RULES["include"]:
        search_pattern = os.path.join(root, pattern)
        files += glob.glob(search_pattern, recursive=True)
    files = [f for f in files if not any(x in f for x in SCAN_RULES["exclude"])]
    return f"扫描完成，发现 {len(files)} 个文件"

def read_file(params):
    path = assert_in_sandbox(normalize_path(params.get("path", "")))
    if not os.path.exists(path): return f"错误：文件不存在 - {path}"
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return content[:5000] + ("..." if len(content) > 5000 else "")
    except Exception as e: return f"读取失败: {str(e)}"

def write_file(params):
    path = assert_in_sandbox(normalize_path(params.get("path", "")))
    content = params.get("content", "")
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        safe_write(path, content)
        return f"文件已写入: {path}"
    except Exception as e: return f"写入失败: {str(e)}"

def run_shell(params):
    command = params.get("command", "")
    try:
        result = run_cross_platform_cmd(command)
        return f"输出:\n{result.stdout[:2000]}\n错误:\n{result.stderr[:500]}"
    except Exception as e: return f"执行失败: {str(e)}"

def call_skill(params):
    """调用已封装的技能库能力"""
    name = params.get("name")
    skill_params = params.get("params", {})
    if not name: return "❌ 缺少技能名称"
    return skill_manager.execute_skill(name, skill_params)

def learn_skill(params):
    """将新能力封装为技能存入库中"""
    name = params.get("name")
    desc = params.get("description")
    code = params.get("code")
    usage = params.get("usage_example", {})
    if not all([name, desc, code]): return "❌ 缺少必要参数"
    return skill_manager.create_skill(name, desc, code, usage)

# ==================== 工具注册表 (元认知增强) ====================

TOOLS = {
    "scan_files": {
        "func": scan_files,
        "desc": "扫描项目文件结构",
        "meta": {
            "usage": "在任务开始时了解项目结构或寻找特定文件",
            "risk": "低",
            "platform": "跨平台通用"
        }
    },
    "read_file": {
        "func": read_file,
        "desc": "读取文件内容",
        "meta": {
            "usage": "查看代码、配置或日志文件",
            "risk": "低",
            "platform": "跨平台通用"
        }
    },
    "write_file": {
        "func": write_file,
        "desc": "写入或修改文件",
        "meta": {
            "usage": "更新代码、保存配置或生成报告",
            "risk": "中 (可能覆盖重要文件)",
            "platform": "跨平台通用"
        }
    },
    "run_shell": {
        "func": run_shell,
        "desc": "执行系统命令",
        "meta": {
            "usage": "运行测试、安装依赖或执行 Git 操作",
            "risk": "高 (需确保命令安全)",
            "platform": "自动转换 (ls->dir, rm->del 等)"
        }
    },
    "call_skill": {
        "func": call_skill,
        "desc": "调用技能库中的扩展能力",
        "meta": {
            "usage": "使用已学习到的复杂技能",
            "risk": "中",
            "platform": "跨平台通用"
        }
    },
    "learn_skill": {
        "func": learn_skill,
        "desc": "将新能力封装为永久技能",
        "meta": {
            "usage": "当完成一个复杂任务后，将其封装以便下次直接调用",
            "risk": "低",
            "platform": "跨平台通用"
        }
    }
}

# 集成自我修改工具
if SELF_MODIFY_AVAILABLE:
    from self_modify import get_or_create_session, request_restart
    TOOLS.update({
        "self_modify_start": {"func": lambda p: get_or_create_session().start_session()[1], "desc": "启动自我修改会话", "meta": {"usage": "开始代码重构或工具安装", "risk": "低", "platform": "通用"}},
        "self_modify_apply": {"func": lambda p: get_or_create_session().apply_modifications(force=p.get("force", False))[1], "desc": "应用代码修改", "meta": {"usage": "将影子环境的代码同步到主系统", "risk": "高", "platform": "通用"}},
        "self_modify_restart": {"func": lambda p: request_restart()[1], "desc": "重启服务", "meta": {"usage": "使新代码或工具生效", "risk": "中", "platform": "通用"}}
    })

def get_available_tools_with_meta():
    """返回包含元数据的工具描述，包括动态加载的技能"""
    all_tools = {name: {"desc": info["desc"], "meta": info["meta"]} for name, info in TOOLS.items()}
    
    # 动态加载技能并注入到工具列表
    skills = skill_manager.scan_skills()
    for name, info in skills.items():
        all_tools[f"skill_{name}"] = {
            "desc": f"[技能] {info['description']}",
            "meta": {
                "usage": f"调用封装技能: {name}",
                "risk": "中",
                "platform": "通用",
                "is_skill": True,
                "params_template": info["usage"]
            }
        }
    return all_tools

def execute(command: str):
    if not command.startswith("RUN"): return "非法格式"
    try:
        payload = json.loads(command[3:].strip())
        tool = payload.get("tool")
        params = payload.get("params", {})
        if tool not in TOOLS: return f"未知工具: {tool}"
        return TOOLS[tool]["func"](params)
    except Exception as e: return f"执行异常: {str(e)}"
