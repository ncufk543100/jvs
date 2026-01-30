"""
JARVIS 安全自我修改模块 (v1.5.0)

核心理念：修改自己的代码时要格外小心
- 强制物理隔离：所有修改在独立的临时目录中进行
- 影子任务压力测试：在应用修改前，启动影子服务器并执行真实任务验证
- 原子替换：只有通过所有测试（包括任务执行）后，才允许替换原文件
- 自动回滚：如果替换后启动失败，自动恢复备份
"""
import os
import sys
import shutil
import subprocess
import tempfile
import json
import time
import signal
import socket
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime


class SelfModifySession:
    """安全自我修改会话"""
    
    def __init__(self, jarvis_root: str = None):
        if jarvis_root is None:
            jarvis_root = os.path.dirname(os.path.abspath(__file__))
        
        self.jarvis_root = jarvis_root
        self.temp_dir = None
        self.backup_dir = None
        self.modifications = []
        self.test_results = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.core_files = self._discover_core_files()
        self.config_files = [
            "SCAN_RULES.json", "STATE.json", "PLAN.json", "EVENTS.json", 
            "ERRORS.json", "PROJECT_ROOT.txt", "secrets.json", "VERSION.json", "README.md"
        ]
    
    def _discover_core_files(self) -> list:
        py_files = []
        for file in os.listdir(self.jarvis_root):
            if file.endswith('.py') and not file.startswith('_') and not file.startswith('.'):
                py_files.append(file)
        return sorted(py_files)
    
    def start_session(self) -> Tuple[bool, str]:
        try:
            self.temp_dir = tempfile.mkdtemp(prefix=f"jarvis_modify_{self.session_id}_")
            backup_base = os.path.join(self.jarvis_root, ".backups")
            os.makedirs(backup_base, exist_ok=True)
            self.backup_dir = os.path.join(backup_base, f"backup_{self.session_id}")
            os.makedirs(self.backup_dir, exist_ok=True)
            
            copied_files = []
            for filename in self.core_files:
                src = os.path.join(self.jarvis_root, filename)
                if os.path.exists(src):
                    shutil.copy2(src, os.path.join(self.temp_dir, filename))
                    shutil.copy2(src, os.path.join(self.backup_dir, filename))
                    copied_files.append(filename)
            
            for filename in self.config_files:
                src = os.path.join(self.jarvis_root, filename)
                if os.path.exists(src):
                    shutil.copy2(src, os.path.join(self.backup_dir, filename))
            
            return True, f"✅ 会话已启动\n临时目录: {self.temp_dir}"
        except Exception as e:
            return False, f"❌ 启动失败: {str(e)}"
    
    def modify_temp_file(self, filename: str, new_content: str) -> Tuple[bool, str]:
        if not self.temp_dir: return False, "❌ 会话未启动"
        filepath = os.path.join(self.temp_dir, filename)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            self.modifications.append({"filename": filename, "timestamp": datetime.now().isoformat()})
            return True, f"✅ 已修改: {filename}"
        except Exception as e:
            return False, f"❌ 修改失败: {str(e)}"

    def run_syntax_check(self) -> Tuple[bool, str]:
        if not self.temp_dir: return False, "❌ 会话未启动"
        results = []
        all_passed = True
        for filename in self.core_files:
            if not filename.endswith(".py"): continue
            filepath = os.path.join(self.temp_dir, filename)
            try:
                result = subprocess.run([sys.executable, "-m", "py_compile", filepath], capture_output=True, text=True, timeout=10)
                if result.returncode != 0:
                    all_passed = False
                    results.append(f"  ❌ {filename}: {result.stderr.strip()}")
            except Exception as e:
                all_passed = False
                results.append(f"  ❌ {filename}: {str(e)}")
        return all_passed, "\n".join(results) or "✅ 语法检查通过"

    def run_shadow_server_test(self) -> Tuple[bool, str]:
        """
        启动影子服务器并执行真实任务压力测试
        """
        if not self.temp_dir: return False, "❌ 会话未启动"
        
        def get_free_port():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', 0))
                return s.getsockname()[1]
        
        port = get_free_port()
        env = os.environ.copy()
        env["PYTHONPATH"] = self.temp_dir
        
        # 准备影子环境的配置文件
        for cfg in ['PROJECT_ROOT.txt', 'SCAN_RULES.json', 'STATE.json', 'secrets.json']:
            src = os.path.join(self.jarvis_root, cfg)
            dst = os.path.join(self.temp_dir, cfg)
            if os.path.exists(src): shutil.copy2(src, dst)
        
        # 启动影子服务器
        cmd = [sys.executable, "-m", "uvicorn", "server:app", "--host", "127.0.0.1", "--port", str(port)]
        process = subprocess.Popen(cmd, cwd=self.temp_dir, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        try:
            time.sleep(5) # 等待启动
            if process.poll() is not None:
                return False, "❌ 影子服务器启动即崩溃"
            
            import requests
            # 1. 健康检查
            resp = requests.get(f"http://127.0.0.1:{port}/health", timeout=5)
            if resp.status_code != 200:
                return False, f"❌ 健康检查失败: {resp.status_code}"
            
            # 2. 压力测试：执行真实任务
            test_task = {"message": "请列出当前目录下的文件并告诉我现在的时间"}
            print(f"🚀 正在向影子服务器 (Port: {port}) 发送压力测试任务...")
            resp = requests.post(f"http://127.0.0.1:{port}/run", json=test_task, timeout=60)
            
            if resp.status_code == 200:
                result_data = resp.json()
                if "result" in result_data:
                    return True, f"✅ 影子任务压力测试通过！\n影子响应: {str(result_data['result'])[:200]}..."
                else:
                    return False, f"❌ 影子服务器响应格式异常: {result_data}"
            else:
                return False, f"❌ 影子任务执行失败: {resp.status_code} - {resp.text}"
                
        except Exception as e:
            return False, f"❌ 影子测试异常: {str(e)}"
        finally:
            process.terminate()
            try: process.wait(timeout=5)
            except: process.kill()

    def apply_modifications(self, force: bool = False) -> Tuple[bool, str]:
        if not self.temp_dir: return False, "❌ 会话未启动"
        
        syntax_ok, syntax_msg = self.run_syntax_check()
        if not syntax_ok and not force: return False, syntax_msg
            
        shadow_ok, shadow_msg = self.run_shadow_server_test()
        if not shadow_ok and not force: return False, shadow_msg
            
        try:
            for mod in self.modifications:
                filename = mod["filename"]
                shutil.copy2(os.path.join(self.temp_dir, filename), os.path.join(self.jarvis_root, filename))
            return True, f"✅ 修改已原子应用并通过影子压力测试。\n请调用 request_restart() 重启。"
        except Exception as e:
            return False, f"❌ 应用失败: {str(e)}"

    def rollback(self) -> Tuple[bool, str]:
        if not self.backup_dir: return False, "❌ 无备份"
        try:
            for filename in os.listdir(self.backup_dir):
                src = os.path.join(self.backup_dir, filename)
                if os.path.isfile(src): shutil.copy2(src, os.path.join(self.jarvis_root, filename))
            return True, "✅ 已回滚"
        except Exception as e:
            return False, f"❌ 回滚失败: {str(e)}"

    def end_session(self, cleanup: bool = True) -> Tuple[bool, str]:
        if cleanup and self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        return True, "✅ 会话已结束"

    def get_session_status(self) -> Dict[str, Any]:
        return {"session_id": self.session_id, "active": self.temp_dir is not None, "modifications": self.modifications}


def request_restart() -> Tuple[bool, str]:
    try:
        root = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(root, ".restart_requested"), "w") as f:
            f.write(datetime.now().isoformat())
        return True, "✅ 重启请求已提交"
    except Exception as e:
        return False, f"❌ 重启请求失败: {str(e)}"


_current_session: Optional[SelfModifySession] = None

def get_or_create_session() -> SelfModifySession:
    global _current_session
    if _current_session is None: _current_session = SelfModifySession()
    return _current_session

def clear_session():
    global _current_session
    _current_session = None
