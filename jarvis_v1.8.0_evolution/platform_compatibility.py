"""
JARVIS 跨平台兼容性工具模块 (v1.5.1)
提供路径处理、命令转换、进程管理等通用函数，支持 Linux 和 Windows 11。
"""
import os
import sys
import platform
import subprocess
from pathlib import Path
from typing import List, Union, Optional

def is_windows() -> bool:
    return os.name == 'nt' or platform.system() == 'Windows'

def normalize_path(path: Union[str, Path]) -> str:
    """将路径转换为当前系统的标准格式"""
    p = Path(path)
    return str(p.absolute()) if p.is_absolute() else str(p)

def get_shell_cmd(cmd: str) -> str:
    """根据系统转换 shell 命令"""
    if not is_windows():
        return cmd
    
    # 简单的命令转换逻辑
    cmd_map = {
        'ls': 'dir',
        'rm -rf': 'rd /s /q',
        'rm': 'del /f /q',
        'cp': 'copy',
        'mv': 'move',
        'mkdir -p': 'mkdir',
        'grep': 'findstr',
        'cat': 'type',
        'pwd': 'cd',
        'clear': 'cls'
    }
    
    for linux_cmd, win_cmd in cmd_map.items():
        if cmd.startswith(linux_cmd):
            return cmd.replace(linux_cmd, win_cmd, 1)
    return cmd

def run_cross_platform_cmd(cmd: Union[str, List[str]], cwd: Optional[str] = None) -> subprocess.CompletedProcess:
    """执行跨平台命令"""
    shell = isinstance(cmd, str)
    if shell and is_windows():
        cmd = get_shell_cmd(cmd)
    
    return subprocess.run(
        cmd,
        shell=shell,
        capture_output=True,
        text=True,
        cwd=cwd,
        encoding='utf-8',
        errors='ignore'
    )

def get_python_executable() -> str:
    """获取当前系统的 Python 解释器路径"""
    return sys.executable
