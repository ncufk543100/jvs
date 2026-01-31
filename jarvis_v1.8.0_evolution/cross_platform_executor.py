import os
import sys
import json
import glob
import datetime
import subprocess
import re
from collections import Counter
from pathlib import Path
from typing import Dict, Any, List, Optional

from sandbox import assert_in_sandbox
from safe_io import safe_write, safe_write_json
from agent_sovereignty import check_venv_for_command
from platform_utils import PlatformUtils

STATE_FILE = "STATE.json"
SCAN_RULES = json.load(open("SCAN_RULES.json", encoding="utf-8"))
PROJECT_MAP_JSON = "PROJECT_MAP.json"
PROJECT_MAP_MD = "PROJECT_MAP.md"

class CrossPlatformExecutor:
    @staticmethod
    def scan_files(params: Optional[Dict[str, Any]] = None) -> str:
        if params and "path" in params:
            root = params["path"]
        else:
            root = SCAN_RULES.get("root") or "."
        
        root_path = Path(root)
        files = []
        for pattern in SCAN_RULES["include"]:
            pattern_path = root_path / pattern
            files += glob.glob(str(pattern_path), recursive=True)
        
        files = [
            assert_in_sandbox(f)
            for f in files
            if not any(x.replace("**/", "") in f for x in SCAN_RULES["exclude"])
        ]
        
        state = json.load(open(STATE_FILE, encoding="utf-8"))
        state["files_touched"] = files
        safe_write_json(STATE_FILE, state)
        return f"扫描完成，发现 {len(files)} 个文件"
    
    @staticmethod
    def generate_project_map(params: Optional[Dict[str, Any]] = None) -> str:
        state = json.load(open(STATE_FILE, encoding="utf-8"))
        files = state.get("files_touched", [])
        
        by_ext = Counter([Path(f).suffix or "no_ext" for f in files])
        data = {
            "root": open("PROJECT_ROOT.txt").read().strip(),
            "files": files,
            "summary": {
                "total_files": len(files),
                "by_ext": dict(by_ext)
            },
            "generated_at": datetime.datetime.now().isoformat()
        }
        safe_write_json(PROJECT_MAP_JSON, data)
        
        lines = [
            f"# 项目地图",
            f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"## 文件统计",
            f"- 总文件数: {len(files)}",
            f"- 按扩展名分类:",
        ]
        for ext, count in sorted(by_ext.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  - {ext}: {count}")
        
        safe_write(PROJECT_MAP_MD, "\n".join(lines))
        return "项目地图已生成"
    
    @staticmethod
    def run_shell(params: Dict[str, Any]) -> str:
        command = params.get("command", "")
        if not command:
            return "错误：缺少command参数"
        
        if PlatformUtils.is_windows():
            command = command.replace("/", "\\")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            output = result.stdout
            if result.stderr:
                output += "\n错误输出:\n" + result.stderr
            return output
        except Exception as e:
            return f"执行命令失败: {e}"
    
    @staticmethod
    def list_files(params: Dict[str, Any]) -> str:
        path = params.get("path", ".")
        path_obj = Path(path)
        
        if not path_obj.exists():
            return f"路径不存在: {path}"
        
        items = []
        for item in path_obj.iterdir():
            if item.is_dir():
                items.append(f"📁 {item.name}/")
            else:
                size = item.stat().st_size
                items.append(f"📄 {item.name} ({size} bytes)")
        
        return "\n".join(sorted(items))
    
    @staticmethod
    def read_file(params: Dict[str, Any]) -> str:
        path = params.get("path", "")
        if not path:
            return "错误：缺少path参数"
        
        path_obj = Path(path)
        if not path_obj.exists():
            return f"文件不存在: {path}"
        
        try:
            content = path_obj.read_text(encoding="utf-8", errors="ignore")
            return content
        except Exception as e:
            return f"读取文件失败: {e}"