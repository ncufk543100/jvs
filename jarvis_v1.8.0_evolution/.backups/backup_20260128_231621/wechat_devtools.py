"""
ClawedBot 微信开发者工具集成模块
自动发现、配置和调用微信开发者工具 CLI
"""
import os
import subprocess
import json
import time
import platform
import re
from pathlib import Path
from typing import Optional, Dict, List, Any

from safe_io import safe_write_json, safe_read_json

_ROOT = Path(__file__).parent
WECHAT_CONFIG_FILE = _ROOT / "WECHAT_CONFIG.json"

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


def get_system_type() -> str:
    """获取操作系统类型"""
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system == "darwin":
        return "mac"
    return "linux"


def find_devtools_cli() -> Optional[str]:
    """自动查找微信开发者工具 CLI 路径"""
    config = load_config()
    if config.get("cli_path") and os.path.exists(config["cli_path"]):
        return config["cli_path"]
    
    system = get_system_type()
    search_paths = WINDOWS_PATHS if system == "windows" else MAC_PATHS
    
    for path in search_paths:
        if os.path.exists(path):
            save_config({"cli_path": path})
            return path
    
    if system == "windows":
        found = search_windows_devtools()
        if found:
            save_config({"cli_path": found})
            return found
    
    return None


def search_windows_devtools() -> Optional[str]:
    """在 Windows 系统中搜索微信开发者工具"""
    try:
        for base in ["C:\\Program Files", "C:\\Program Files (x86)", 
                     "D:\\Program Files", "D:\\Program Files (x86)"]:
            if os.path.exists(base):
                for item in os.listdir(base):
                    if "微信" in item and "开发者工具" in item:
                        cli_path = os.path.join(base, item, "cli.bat")
                        if os.path.exists(cli_path):
                            return cli_path
    except Exception:
        pass
    return None


def load_config() -> dict:
    """加载微信开发者工具配置"""
    return safe_read_json(str(WECHAT_CONFIG_FILE), default={
        "cli_path": None, "project_path": None, "service_port": None
    })


def save_config(updates: dict) -> None:
    """保存配置更新"""
    config = load_config()
    config.update(updates)
    safe_write_json(str(WECHAT_CONFIG_FILE), config)


def run_cli_command(args: List[str], timeout: int = 60) -> Dict[str, Any]:
    """执行微信开发者工具 CLI 命令"""
    cli_path = find_devtools_cli()
    if not cli_path:
        return {
            "success": False, "output": "",
            "error": "未找到微信开发者工具 CLI，请确保已安装"
        }
    
    try:
        cmd = [cli_path] + args
        result = subprocess.run(cmd, capture_output=True, text=True, 
                               timeout=timeout, encoding="utf-8", errors="ignore")
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "", "error": f"命令执行超时（{timeout}秒）"}
    except Exception as e:
        return {"success": False, "output": "", "error": f"执行失败: {e}"}


# ==================== 核心功能 ====================

def check_devtools_status() -> Dict[str, Any]:
    """检查微信开发者工具状态"""
    cli_path = find_devtools_cli()
    status = {
        "installed": cli_path is not None,
        "cli_path": cli_path,
        "service_running": False
    }
    
    if cli_path:
        result = run_cli_command(["--version"], timeout=10)
        status["service_running"] = result["success"]
    
    return status


def open_devtools(project_path: str = None) -> Dict[str, Any]:
    """打开微信开发者工具"""
    args = ["open"]
    if project_path:
        args.extend(["--project", project_path])
        save_config({"project_path": project_path})
    return run_cli_command(args, timeout=30)


def get_project_info(project_path: str = None) -> Dict[str, Any]:
    """获取小程序项目信息"""
    if not project_path:
        config = load_config()
        project_path = config.get("project_path")
    
    if not project_path:
        return {"success": False, "error": "未指定项目路径"}
    
    config_file = os.path.join(project_path, "project.config.json")
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                project_config = json.load(f)
            return {
                "success": True,
                "project_path": project_path,
                "appid": project_config.get("appid"),
                "project_name": project_config.get("projectname"),
                "config": project_config
            }
        except Exception as e:
            return {"success": False, "error": f"读取项目配置失败: {e}"}
    
    return {"success": False, "error": f"项目配置文件不存在: {config_file}"}


def build_npm(project_path: str = None) -> Dict[str, Any]:
    """构建 npm"""
    if not project_path:
        config = load_config()
        project_path = config.get("project_path")
    
    if not project_path:
        return {"success": False, "error": "未指定项目路径"}
    
    return run_cli_command(["build-npm", "--project", project_path], timeout=120)


def preview(project_path: str = None, qr_format: str = "terminal") -> Dict[str, Any]:
    """预览小程序"""
    if not project_path:
        config = load_config()
        project_path = config.get("project_path")
    
    if not project_path:
        return {"success": False, "error": "未指定项目路径"}
    
    args = ["preview", "--project", project_path]
    if qr_format == "base64":
        args.extend(["--qr-format", "base64"])
    elif qr_format == "image":
        qr_path = os.path.join(project_path, "preview_qr.png")
        args.extend(["--qr-format", "image", "--qr-output", qr_path])
    
    result = run_cli_command(args, timeout=120)
    if qr_format == "image" and result["success"]:
        result["qr_path"] = qr_path
    
    return result


def upload(project_path: str = None, version: str = "1.0.0", desc: str = "自动上传") -> Dict[str, Any]:
    """上传小程序代码"""
    if not project_path:
        config = load_config()
        project_path = config.get("project_path")
    
    if not project_path:
        return {"success": False, "error": "未指定项目路径"}
    
    args = ["upload", "--project", project_path, "-v", version, "-d", desc]
    return run_cli_command(args, timeout=180)


def get_compile_errors(project_path: str = None) -> Dict[str, Any]:
    """获取编译错误"""
    if not project_path:
        config = load_config()
        project_path = config.get("project_path")
    
    if not project_path:
        return {"success": False, "error": "未指定项目路径"}
    
    log_paths = [
        os.path.join(project_path, ".wechat_devtools", "compile.log"),
        os.path.join(project_path, "compile_errors.log"),
    ]
    
    errors = []
    for log_path in log_paths:
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    error_patterns = [r"Error:.*", r"error:.*", r"TypeError:.*", r"SyntaxError:.*"]
                    for pattern in error_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        errors.extend(matches)
            except Exception:
                pass
    
    return {"success": True, "errors": errors, "count": len(errors)}


def take_screenshot(project_path: str = None, output_path: str = None) -> Dict[str, Any]:
    """截取小程序截图"""
    if not project_path:
        config = load_config()
        project_path = config.get("project_path")
    
    if not project_path:
        return {"success": False, "error": "未指定项目路径"}
    
    if not output_path:
        output_path = os.path.join(project_path, f"screenshot_{int(time.time())}.png")
    
    result = run_cli_command([
        "auto", "--project", project_path,
        "--auto-port", "9420", "--screenshot", output_path
    ], timeout=30)
    
    if result["success"] and os.path.exists(output_path):
        result["screenshot_path"] = output_path
    
    return result


def close_devtools() -> Dict[str, Any]:
    """关闭微信开发者工具"""
    return run_cli_command(["close"], timeout=10)


# ==================== 工具函数（供 executor 调用）====================

def wechat_check_status(params: dict = None) -> str:
    """检查微信开发者工具状态"""
    status = check_devtools_status()
    
    if status["installed"]:
        return f"""微信开发者工具状态:
✅ 已安装
📍 CLI 路径: {status['cli_path']}
🔌 服务状态: {'运行中' if status['service_running'] else '未运行'}"""
    else:
        return """微信开发者工具状态:
❌ 未找到微信开发者工具
请确保已安装微信开发者工具"""


def wechat_open(params: dict) -> str:
    """打开微信开发者工具"""
    project_path = params.get("project_path")
    result = open_devtools(project_path)
    
    if result["success"]:
        return f"✅ 微信开发者工具已打开" + (f"\n项目: {project_path}" if project_path else "")
    return f"❌ 打开失败: {result['error']}"


def wechat_get_errors(params: dict) -> str:
    """获取编译错误"""
    project_path = params.get("project_path")
    result = get_compile_errors(project_path)
    
    if result["errors"]:
        errors_text = "\n".join(f"- {e}" for e in result["errors"][:20])
        return f"发现 {result['count']} 个错误:\n{errors_text}"
    return "✅ 没有发现编译错误"


def wechat_preview(params: dict) -> str:
    """预览小程序"""
    project_path = params.get("project_path")
    result = preview(project_path)
    
    if result["success"]:
        return f"✅ 预览成功\n{result['output']}"
    return f"❌ 预览失败: {result['error']}"


def wechat_upload(params: dict) -> str:
    """上传小程序"""
    project_path = params.get("project_path")
    version = params.get("version", "1.0.0")
    desc = params.get("desc", "自动上传")
    
    result = upload(project_path, version, desc)
    
    if result["success"]:
        return f"✅ 上传成功\n版本: {version}\n描述: {desc}"
    return f"❌ 上传失败: {result['error']}"


def wechat_screenshot(params: dict) -> str:
    """截取小程序截图"""
    project_path = params.get("project_path")
    output_path = params.get("output_path")
    
    result = take_screenshot(project_path, output_path)
    
    if result["success"] and result.get("screenshot_path"):
        return f"✅ 截图已保存: {result['screenshot_path']}"
    return f"❌ 截图失败: {result.get('error', '未知错误')}"


if __name__ == "__main__":
    print("检查微信开发者工具状态...")
    print(wechat_check_status())
