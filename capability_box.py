"""
能力沙盒系统 (Capability Box)
核心原则：不限制思想，只限制手脚
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional


class CapabilityBox:
    """
    能力沙盒：定义 AI 的物理边界
    
    核心思想：
    - AI 可以自主生成任何目标
    - AI 可以自主决定任何策略
    - 但所有行为必须在能力边界内
    """
    
    def __init__(self, workspace: str = None):
        self.workspace = workspace or os.path.dirname(os.path.abspath(__file__))
        self.project_root = self.workspace
        
        # 允许的文件操作范围
        self.allowed_paths = [
            self.workspace,
            "/tmp",
            os.path.expanduser("~/.jarvis")
        ]
        
        # 禁止的路径（绝对禁止）
        self.forbidden_paths = [
            "/",
            "/home",
            "/etc",
            "/usr",
            "/var",
            "/sys",
            "/proc",
            "/boot"
        ]
        
        # 允许的命令白名单
        self.allowed_commands = [
            "python", "python3", "pip", "pip3",
            "git", "npm", "node", "pnpm",
            "ls", "cat", "echo", "mkdir", "touch",
            "curl", "wget", "grep", "find",
            "pytest", "black", "flake8", "mypy"
        ]
        
        # 允许安装的包（白名单）
        self.allowed_packages = [
            # AI/ML
            "openai", "anthropic", "transformers",
            # 数据处理
            "pandas", "numpy", "scipy",
            # Web
            "requests", "beautifulsoup4", "selenium",
            # 工具
            "pytest", "black", "flake8", "mypy",
            # TTS/ASR
            "gpt-sovits", "whisper", "pyttsx3",
            # 其他
            "*"  # 暂时允许所有，后续可以收紧
        ]
        
        # 资源限制
        self.resource_limits = {
            "max_file_size": 100 * 1024 * 1024,  # 100MB
            "max_memory": 2 * 1024 * 1024 * 1024,  # 2GB
            "max_processes": 10
        }
    
    def can_read(self, path: str) -> bool:
        """检查是否可以读取文件"""
        abs_path = os.path.abspath(path)
        
        # 检查是否在禁止路径
        for forbidden in self.forbidden_paths:
            if abs_path.startswith(forbidden + "/") or abs_path == forbidden:
                return False
        
        # 检查是否在允许路径
        for allowed in self.allowed_paths:
            if abs_path.startswith(allowed + "/") or abs_path == allowed:
                return True
        
        return False
    
    def can_write(self, path: str) -> bool:
        """检查是否可以写入文件"""
        return self.can_read(path)  # 读写权限相同
    
    def can_delete(self, path: str) -> bool:
        """检查是否可以删除文件"""
        abs_path = os.path.abspath(path)
        
        # 删除操作更严格：只能删除工作空间内的文件
        if not abs_path.startswith(self.workspace + "/"):
            return False
        
        # 不能删除关键文件
        critical_files = [
            "agent.py", "capability_box.py", "sandbox.py",
            "VERSION.json", "PROJECT_ROOT.txt"
        ]
        
        filename = os.path.basename(abs_path)
        if filename in critical_files:
            return False
        
        return True
    
    def can_execute(self, command: str) -> bool:
        """检查是否可以执行命令"""
        # 提取命令的第一个词
        cmd = command.strip().split()[0] if command.strip() else ""
        
        # 移除路径前缀
        cmd = os.path.basename(cmd)
        
        # 检查是否在白名单
        return cmd in self.allowed_commands
    
    def can_install(self, package: str) -> bool:
        """检查是否可以安装包"""
        # 暂时允许所有包
        if "*" in self.allowed_packages:
            return True
        
        return package in self.allowed_packages
    
    def sanitize_path(self, path: str) -> str:
        """规范化路径"""
        # 如果是相对路径，转换为相对于工作空间的绝对路径
        if not os.path.isabs(path):
            path = os.path.join(self.workspace, path)
        
        return os.path.abspath(path)
    
    def check_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        检查动作是否在能力边界内
        
        返回：
        {
            "allowed": bool,
            "reason": str,
            "alternative": Optional[Dict]
        }
        """
        action_type = action.get("type")
        
        if action_type == "read_file":
            path = self.sanitize_path(action.get("path", ""))
            if self.can_read(path):
                return {"allowed": True}
            else:
                return {
                    "allowed": False,
                    "reason": f"路径 {path} 不在允许的读取范围内"
                }
        
        elif action_type == "write_file":
            path = self.sanitize_path(action.get("path", ""))
            if self.can_write(path):
                return {"allowed": True}
            else:
                return {
                    "allowed": False,
                    "reason": f"路径 {path} 不在允许的写入范围内"
                }
        
        elif action_type == "delete_file":
            path = self.sanitize_path(action.get("path", ""))
            if self.can_delete(path):
                return {"allowed": True}
            else:
                return {
                    "allowed": False,
                    "reason": f"不允许删除 {path}"
                }
        
        elif action_type == "run_command":
            command = action.get("command", "")
            if self.can_execute(command):
                return {"allowed": True}
            else:
                return {
                    "allowed": False,
                    "reason": f"命令 {command.split()[0]} 不在白名单中"
                }
        
        elif action_type == "install_package":
            package = action.get("package", "")
            if self.can_install(package):
                return {"allowed": True}
            else:
                return {
                    "allowed": False,
                    "reason": f"包 {package} 不在允许安装列表中"
                }
        
        # 默认允许
        return {"allowed": True}
    
    def get_capability_report(self) -> Dict[str, Any]:
        """获取能力边界报告"""
        return {
            "workspace": self.workspace,
            "allowed_paths": self.allowed_paths,
            "forbidden_paths": self.forbidden_paths,
            "allowed_commands": self.allowed_commands,
            "allowed_packages": self.allowed_packages,
            "resource_limits": self.resource_limits
        }


# 全局单例
_capability_box = None

def get_capability_box() -> CapabilityBox:
    """获取全局能力沙盒实例"""
    global _capability_box
    if _capability_box is None:
        _capability_box = CapabilityBox()
    return _capability_box
