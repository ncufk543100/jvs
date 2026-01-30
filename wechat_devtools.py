"""
JARVIS 微信开发者工具集成模块 (v1.5.4)
支持跨平台自动发现、配置和调用微信开发者工具 CLI。
"""
import os
import subprocess
import json
import time
import platform
import re
from pathlib import Path
from typing import Optional, Dict, List, Any

# 导入跨平台工具
from platform_compatibility import normalize_path, is_windows
from safe_io import safe_write_json, safe_read_json

_ROOT = Path(__file__).parent.absolute()
WECHAT_CONFIG_FILE = normalize_path(_ROOT / "WECHAT_CONFIG.json")

# 默认安装路径
WINDOWS_PATHS = [
    r"C:\Program Files (x86)\Tencent\微信web开发者工具\cli.bat",
    r"C:\Program Files\Tencent\微信web开发者工具\cli.bat",
    r"D:\Program Files (x86)\Tencent\微信web开发者工具\cli.bat",
    r"D:\Program Files\Tencent\微信web开发者工具\cli.bat",
]

MAC_PATHS = [
    "/Applications/wechatwebdevtools.app/Contents/MacOS/cli",
    "/Applications/微信web开发者工具.app/Contents/MacOS/cli",
]

def find_devtools_cli() -> Optional[str]:
    """自动查找微信开发者工具 CLI 路径"""
    config = safe_read_json(WECHAT_CONFIG_FILE, default={})
    if config.get("cli_path") and os.path.exists(config["cli_path"]):
        return config["cli_path"]
    
    search_paths = WINDOWS_PATHS if is_windows() else MAC_PATHS
    for path in search_paths:
        if os.path.exists(path):
            safe_write_json(WECHAT_CONFIG_FILE, {"cli_path": path})
            return path
    
    if is_windows():
        # 深度搜索逻辑
        for base in [r"C:\Program Files", r"C:\Program Files (x86)", r"D:\Program Files"]:
            if os.path.exists(base):
                try:
                    for item in os.listdir(base):
                        if "微信" in item and "开发者工具" in item:
                            cli_path = os.path.join(base, item, "cli.bat")
                            if os.path.exists(cli_path):
                                safe_write_json(WECHAT_CONFIG_FILE, {"cli_path": cli_path})
                                return cli_path
                except: pass
    return None

def run_cli_command(args: List[str], timeout: int = 60) -> Dict[str, Any]:
    cli_path = find_devtools_cli()
    if not cli_path:
        return {"success": False, "error": "未找到微信开发者工具 CLI"}
    
    try:
        cmd = [cli_path] + args
        result = subprocess.run(cmd, capture_output=True, text=True, 
                               timeout=timeout, encoding="utf-8", errors="ignore")
        return {"success": result.returncode == 0, "output": result.stdout, "error": result.stderr}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==================== 核心功能 ====================

def wechat_check_status(params: dict = None) -> str:
    cli_path = find_devtools_cli()
    if cli_path:
        return f"✅ 微信开发者工具已安装\n📍 路径: {cli_path}"
    return "❌ 未找到微信开发者工具"

def wechat_open(params: dict) -> str:
    project_path = params.get("project_path")
    args = ["open"]
    if project_path: args.extend(["--project", normalize_path(project_path)])
    result = run_cli_command(args)
    return "✅ 已打开" if result["success"] else f"❌ 失败: {result['error']}"

def wechat_preview(params: dict) -> str:
    project_path = params.get("project_path")
    if not project_path: return "❌ 缺少项目路径"
    result = run_cli_command(["preview", "--project", normalize_path(project_path)])
    return f"✅ 预览成功\n{result['output']}" if result["success"] else f"❌ 失败: {result['error']}"

def wechat_upload(params: dict) -> str:
    project_path = params.get("project_path")
    version = params.get("version", "1.0.0")
    desc = params.get("desc", "自动上传")
    if not project_path: return "❌ 缺少项目路径"
    result = run_cli_command(["upload", "--project", normalize_path(project_path), "-v", version, "-d", desc])
    return f"✅ 上传成功" if result["success"] else f"❌ 失败: {result['error']}"

if __name__ == "__main__":
    print(wechat_check_status())
