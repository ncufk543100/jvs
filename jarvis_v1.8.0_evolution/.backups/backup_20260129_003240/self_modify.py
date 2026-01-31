"""
JARVIS 安全自我修改模块

核心理念：修改自己的代码时要格外小心
- 先复制到临时目录
- 在副本上进行修改
- 运行测试验证
- 测试通过后才覆盖原文件
- 然后重启服务

这样即使修改出错，也不会影响正在运行的系统
"""
import os
import sys
import shutil
import subprocess
import tempfile
import json
import time
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime


class SelfModifySession:
    """安全自我修改会话"""
    
    def __init__(self, clawedbot_root: str = None):
        """
        初始化自我修改会话
        
        Args:
            clawedbot_root: JARVIS 代码根目录，默认为当前文件所在目录
        """
        if clawedbot_root is None:
            clawedbot_root = os.path.dirname(os.path.abspath(__file__))
        
        self.clawedbot_root = clawedbot_root
        self.temp_dir = None
        self.backup_dir = None
        self.modifications = []  # 记录所有修改
        self.test_results = []   # 记录测试结果
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JARVIS 核心文件列表
        self.core_files = [
            "agent.py",
            "executor.py",
            "llm.py",
            "server.py",
            "sandbox.py",
            "safe_io.py",
            "config.py",
            "event_bus.py",
            "run_lock.py",
            "memory_manager.py",
            "agent_sovereignty.py",
            "agent_conclusion.py",
            "user_preferences.py",
            "long_term_memory.py",
            "wechat_devtools.py",
            "POST_RUN_REPORTER.py",
            "self_modify.py",  # 包括自己
        ]
        
        # 配置文件
        self.config_files = [
            "SCAN_RULES.json",
            "STATE.json",
            "PLAN.json",
            "EVENTS.json",
            "ERRORS.json",
            "PROJECT_ROOT.txt",
            "secrets.json",
        ]
    
    def start_session(self) -> Tuple[bool, str]:
        """
        开始自我修改会话
        
        1. 创建临时目录
        2. 复制所有代码到临时目录
        3. 创建备份
        
        Returns:
            (成功与否, 消息)
        """
        try:
            # 创建临时工作目录
            self.temp_dir = tempfile.mkdtemp(prefix=f"clawedbot_modify_{self.session_id}_")
            
            # 创建备份目录
            backup_base = os.path.join(self.clawedbot_root, ".backups")
            os.makedirs(backup_base, exist_ok=True)
            self.backup_dir = os.path.join(backup_base, f"backup_{self.session_id}")
            os.makedirs(self.backup_dir, exist_ok=True)
            
            # 复制核心文件到临时目录和备份目录
            copied_files = []
            for filename in self.core_files:
                src = os.path.join(self.clawedbot_root, filename)
                if os.path.exists(src):
                    # 复制到临时目录
                    dst_temp = os.path.join(self.temp_dir, filename)
                    shutil.copy2(src, dst_temp)
                    
                    # 复制到备份目录
                    dst_backup = os.path.join(self.backup_dir, filename)
                    shutil.copy2(src, dst_backup)
                    
                    copied_files.append(filename)
            
            # 复制配置文件到备份（不复制到临时目录，因为不修改配置）
            for filename in self.config_files:
                src = os.path.join(self.clawedbot_root, filename)
                if os.path.exists(src):
                    dst_backup = os.path.join(self.backup_dir, filename)
                    shutil.copy2(src, dst_backup)
            
            msg = f"""✅ 自我修改会话已启动

会话 ID: {self.session_id}
临时目录: {self.temp_dir}
备份目录: {self.backup_dir}

已复制 {len(copied_files)} 个核心文件到临时目录:
{chr(10).join(['  - ' + f for f in copied_files])}

现在可以安全地修改临时目录中的代码。
修改完成后，请运行测试验证，然后应用修改。"""
            
            return True, msg
            
        except Exception as e:
            return False, f"❌ 启动会话失败: {str(e)}"
    
    def read_temp_file(self, filename: str) -> Tuple[bool, str]:
        """
        读取临时目录中的文件
        
        Args:
            filename: 文件名
        
        Returns:
            (成功与否, 文件内容或错误消息)
        """
        if not self.temp_dir:
            return False, "❌ 会话未启动，请先调用 start_session()"
        
        filepath = os.path.join(self.temp_dir, filename)
        if not os.path.exists(filepath):
            return False, f"❌ 文件不存在: {filename}"
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            return True, content
        except Exception as e:
            return False, f"❌ 读取文件失败: {str(e)}"
    
    def modify_temp_file(self, filename: str, new_content: str) -> Tuple[bool, str]:
        """
        修改临时目录中的文件
        
        Args:
            filename: 文件名
            new_content: 新内容
        
        Returns:
            (成功与否, 消息)
        """
        if not self.temp_dir:
            return False, "❌ 会话未启动，请先调用 start_session()"
        
        filepath = os.path.join(self.temp_dir, filename)
        
        try:
            # 记录修改前的内容
            old_content = ""
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    old_content = f.read()
            
            # 写入新内容
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            # 记录修改
            self.modifications.append({
                "filename": filename,
                "timestamp": datetime.now().isoformat(),
                "old_lines": len(old_content.splitlines()),
                "new_lines": len(new_content.splitlines()),
                "diff_size": abs(len(new_content) - len(old_content))
            })
            
            return True, f"✅ 已修改临时文件: {filename}"
            
        except Exception as e:
            return False, f"❌ 修改文件失败: {str(e)}"
    
    def run_syntax_check(self) -> Tuple[bool, str]:
        """
        对临时目录中的所有 Python 文件进行语法检查
        
        Returns:
            (全部通过与否, 详细结果)
        """
        if not self.temp_dir:
            return False, "❌ 会话未启动"
        
        results = []
        all_passed = True
        
        for filename in self.core_files:
            if not filename.endswith(".py"):
                continue
            
            filepath = os.path.join(self.temp_dir, filename)
            if not os.path.exists(filepath):
                continue
            
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "py_compile", filepath],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    results.append(f"  ✅ {filename}: 语法正确")
                else:
                    all_passed = False
                    error_msg = result.stderr.strip() or "未知错误"
                    results.append(f"  ❌ {filename}: {error_msg}")
                    
            except Exception as e:
                all_passed = False
                results.append(f"  ❌ {filename}: 检查失败 - {str(e)}")
        
        status = "✅ 所有文件语法检查通过" if all_passed else "❌ 部分文件语法检查失败"
        
        self.test_results.append({
            "test": "syntax_check",
            "passed": all_passed,
            "timestamp": datetime.now().isoformat()
        })
        
        return all_passed, f"{status}\n\n" + "\n".join(results)
    
    def run_import_test(self) -> Tuple[bool, str]:
        """
        测试临时目录中的模块是否可以正常导入
        
        Returns:
            (全部通过与否, 详细结果)
        """
        if not self.temp_dir:
            return False, "❌ 会话未启动"
        
        # 复制必要的配置文件到临时目录（用于导入测试）
        import shutil
        for cfg_file in ['PROJECT_ROOT.txt', 'SCAN_RULES.json', 'STATE.json', 'secrets.json']:
            src = os.path.join(self.clawedbot_root, cfg_file)
            dst = os.path.join(self.temp_dir, cfg_file)
            if os.path.exists(src) and not os.path.exists(dst):
                shutil.copy2(src, dst)
        
        # 创建测试脚本
        test_script = f'''
import sys
sys.path.insert(0, "{self.temp_dir}")

results = []
modules = [
    "agent",
    "executor", 
    "llm",
    "server",
    "sandbox",
    "safe_io",
    "config",
    "event_bus",
    "run_lock",
    "memory_manager",
    "agent_sovereignty",
    "agent_conclusion",
    "user_preferences",
    "long_term_memory",
]

for m in modules:
    try:
        __import__(m)
        results.append(f"OK:" + m)
    except Exception as e:
        results.append(f"FAIL:" + m + ":" + str(e)[:100])

print("|||".join(results))
'''
        
        try:
            result = subprocess.run(
                [sys.executable, "-c", test_script],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.temp_dir
            )
            
            output = result.stdout.strip()
            results = []
            all_passed = True
            
            if output:
                for item in output.split("|||"):
                    if item.startswith("OK:"):
                        mod = item[3:]
                        results.append(f"  ✅ {mod}: 导入成功")
                    elif item.startswith("FAIL:"):
                        all_passed = False
                        parts = item[5:].split(":", 1)
                        mod = parts[0]
                        error = parts[1] if len(parts) > 1 else "未知错误"
                        results.append(f"  ❌ {mod}: {error}")
            
            if result.stderr:
                all_passed = False
                results.append(f"\n标准错误输出:\n{result.stderr[:500]}")
            
            status = "✅ 所有模块导入测试通过" if all_passed else "❌ 部分模块导入失败"
            
            self.test_results.append({
                "test": "import_test",
                "passed": all_passed,
                "timestamp": datetime.now().isoformat()
            })
            
            return all_passed, f"{status}\n\n" + "\n".join(results)
            
        except Exception as e:
            self.test_results.append({
                "test": "import_test",
                "passed": False,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            })
            return False, f"❌ 导入测试执行失败: {str(e)}"
    
    def run_custom_test(self, test_code: str) -> Tuple[bool, str]:
        """
        运行自定义测试代码
        
        Args:
            test_code: 测试代码
        
        Returns:
            (测试通过与否, 输出结果)
        """
        if not self.temp_dir:
            return False, "❌ 会话未启动"
        
        # 将测试代码写入临时文件
        test_file = os.path.join(self.temp_dir, "_custom_test.py")
        
        # 添加路径设置
        full_code = f'''
import sys
sys.path.insert(0, "{self.temp_dir}")

{test_code}
'''
        
        try:
            with open(test_file, "w", encoding="utf-8") as f:
                f.write(full_code)
            
            result = subprocess.run(
                [sys.executable, test_file],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.temp_dir
            )
            
            output = ""
            if result.stdout:
                output += f"输出:\n{result.stdout}\n"
            if result.stderr:
                output += f"错误:\n{result.stderr}\n"
            
            passed = result.returncode == 0
            
            self.test_results.append({
                "test": "custom_test",
                "passed": passed,
                "timestamp": datetime.now().isoformat(),
                "return_code": result.returncode
            })
            
            status = "✅ 自定义测试通过" if passed else f"❌ 自定义测试失败 (返回码: {result.returncode})"
            
            return passed, f"{status}\n\n{output}"
            
        except subprocess.TimeoutExpired:
            return False, "❌ 测试执行超时（60秒）"
        except Exception as e:
            return False, f"❌ 测试执行失败: {str(e)}"
        finally:
            # 清理测试文件
            if os.path.exists(test_file):
                os.remove(test_file)
    
    def run_all_tests(self) -> Tuple[bool, str]:
        """
        运行所有标准测试
        
        Returns:
            (全部通过与否, 详细结果)
        """
        results = []
        all_passed = True
        
        # 语法检查
        results.append("### 1. 语法检查")
        passed, msg = self.run_syntax_check()
        results.append(msg)
        if not passed:
            all_passed = False
        
        results.append("")
        
        # 导入测试
        results.append("### 2. 模块导入测试")
        passed, msg = self.run_import_test()
        results.append(msg)
        if not passed:
            all_passed = False
        
        summary = "✅ 所有测试通过，可以安全应用修改" if all_passed else "❌ 部分测试失败，请修复后再应用"
        
        return all_passed, f"## 测试结果\n\n{summary}\n\n" + "\n".join(results)
    
    def apply_modifications(self, force: bool = False) -> Tuple[bool, str]:
        """
        将临时目录中的修改应用到原目录
        
        Args:
            force: 是否强制应用（即使测试未通过）
        
        Returns:
            (成功与否, 消息)
        """
        if not self.temp_dir:
            return False, "❌ 会话未启动"
        
        if not self.modifications:
            return False, "❌ 没有任何修改需要应用"
        
        # 检查测试是否通过
        if not force:
            failed_tests = [t for t in self.test_results if not t.get("passed", False)]
            if failed_tests:
                return False, f"❌ 有 {len(failed_tests)} 个测试未通过，请先修复或使用 force=True 强制应用"
        
        try:
            applied_files = []
            
            for mod in self.modifications:
                filename = mod["filename"]
                src = os.path.join(self.temp_dir, filename)
                dst = os.path.join(self.clawedbot_root, filename)
                
                if os.path.exists(src):
                    shutil.copy2(src, dst)
                    applied_files.append(filename)
            
            msg = f"""✅ 修改已应用

已更新 {len(applied_files)} 个文件:
{chr(10).join(['  - ' + f for f in applied_files])}

备份位置: {self.backup_dir}

⚠️ 注意：修改已应用，但需要重启服务才能生效。
使用 request_restart() 请求重启服务。"""
            
            return True, msg
            
        except Exception as e:
            return False, f"❌ 应用修改失败: {str(e)}"
    
    def rollback(self) -> Tuple[bool, str]:
        """
        回滚到备份版本
        
        Returns:
            (成功与否, 消息)
        """
        if not self.backup_dir or not os.path.exists(self.backup_dir):
            return False, "❌ 没有可用的备份"
        
        try:
            restored_files = []
            
            for filename in os.listdir(self.backup_dir):
                src = os.path.join(self.backup_dir, filename)
                dst = os.path.join(self.clawedbot_root, filename)
                
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
                    restored_files.append(filename)
            
            msg = f"""✅ 已回滚到备份版本

已恢复 {len(restored_files)} 个文件:
{chr(10).join(['  - ' + f for f in restored_files])}

⚠️ 注意：需要重启服务才能生效。"""
            
            return True, msg
            
        except Exception as e:
            return False, f"❌ 回滚失败: {str(e)}"
    
    def end_session(self, cleanup: bool = True) -> Tuple[bool, str]:
        """
        结束自我修改会话
        
        Args:
            cleanup: 是否清理临时目录
        
        Returns:
            (成功与否, 消息)
        """
        try:
            if cleanup and self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            
            summary = {
                "session_id": self.session_id,
                "modifications": len(self.modifications),
                "tests_run": len(self.test_results),
                "tests_passed": sum(1 for t in self.test_results if t.get("passed", False)),
                "temp_dir_cleaned": cleanup
            }
            
            msg = f"""✅ 会话已结束

会话 ID: {self.session_id}
修改数量: {summary['modifications']}
测试数量: {summary['tests_run']}
通过测试: {summary['tests_passed']}
临时目录已清理: {'是' if cleanup else '否'}

备份保留在: {self.backup_dir}"""
            
            return True, msg
            
        except Exception as e:
            return False, f"❌ 结束会话失败: {str(e)}"
    
    def get_session_status(self) -> Dict[str, Any]:
        """获取当前会话状态"""
        return {
            "session_id": self.session_id,
            "active": self.temp_dir is not None,
            "temp_dir": self.temp_dir,
            "backup_dir": self.backup_dir,
            "modifications": self.modifications,
            "test_results": self.test_results,
            "clawedbot_root": self.clawedbot_root
        }


def request_restart() -> Tuple[bool, str]:
    """
    请求重启 JARVIS 服务
    
    这会创建一个重启标记文件，服务器会检测到并重启
    
    Returns:
        (成功与否, 消息)
    """
    try:
        clawedbot_root = os.path.dirname(os.path.abspath(__file__))
        restart_file = os.path.join(clawedbot_root, ".restart_requested")
        
        with open(restart_file, "w") as f:
            f.write(datetime.now().isoformat())
        
        return True, """✅ 重启请求已提交

服务器将在下一个检查周期重启。
如果服务器没有自动重启，请手动执行:
  1. 停止服务: Ctrl+C 或 kill 进程
  2. 重新启动: uvicorn server:app --reload"""
        
    except Exception as e:
        return False, f"❌ 提交重启请求失败: {str(e)}"


# 全局会话实例
_current_session: Optional[SelfModifySession] = None


def get_or_create_session() -> SelfModifySession:
    """获取或创建自我修改会话"""
    global _current_session
    if _current_session is None:
        _current_session = SelfModifySession()
    return _current_session


def clear_session():
    """清除当前会话"""
    global _current_session
    _current_session = None
