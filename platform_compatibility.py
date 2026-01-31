import os
import platform
import subprocess

def is_windows():
    return platform.system().lower() == "windows"

def normalize_path(path):
    if not path:
        return path
    # 修复转义问题，确保路径分隔符正确
    path = str(path).replace("\\", "/")
    return path

def get_shell_cmd(command):
    if is_windows():
        return ["powershell", "-Command", command]
    return ["bash", "-c", command]

def run_cross_platform_cmd(command):
    cmd = get_shell_cmd(command)
    # 确保在 Linux 环境下运行
    return subprocess.run(cmd, capture_output=True, text=True)
