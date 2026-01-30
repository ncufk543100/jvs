"""
韧性执行引擎 (Resilience Engine)
为JARVIS提供智能重试、错误恢复和替代方案能力

核心功能：
1. 智能重试机制
2. 命令输出解析和信息提取
3. 错误分析和自动修复
4. 替代方案生成
5. 执行上下文管理
"""

import re
import os
from typing import Dict, List, Optional, Tuple, Callable
from executor import execute

class ResilienceEngine:
    """韧性执行引擎"""
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.execution_context = {
            "last_outputs": [],
            "extracted_paths": [],
            "extracted_urls": [],
            "extracted_data": {}
        }
    
    def execute_with_resilience(
        self,
        tool: str,
        params: dict,
        reason: str = "",
        emit: Callable = None
    ) -> Tuple[bool, dict]:
        """
        带韧性的工具执行
        
        Returns:
            (success: bool, result: dict)
        """
        if emit is None:
            emit = lambda *args: None
        
        last_error = None
        
        for attempt in range(self.max_retries):
            # 执行工具
            result = execute(tool, params)
            
            # 更新执行上下文
            self._update_context(result)
            
            if result.get("success"):
                return True, result
            
            # 失败，分析原因
            error = result.get("error", "未知错误")
            last_error = error
            
            if attempt < self.max_retries - 1:
                emit("warning", f"⚠️ 尝试 {attempt+1}/{self.max_retries} 失败: {error}")
                
                # 尝试自动修复
                fixed_params = self._try_auto_fix(tool, params, error)
                
                if fixed_params:
                    emit("info", f"💡 尝试修复方案...")
                    params = fixed_params
                    continue
                
                # 尝试替代方案
                alternatives = self._generate_alternatives(tool, params, error)
                
                if alternatives:
                    emit("info", f"💡 尝试替代方案...")
                    for alt in alternatives:
                        alt_result = execute(alt["tool"], alt["params"])
                        self._update_context(alt_result)
                        
                        if alt_result.get("success"):
                            # 替代方案成功，尝试用新信息重试原任务
                            fixed_params = self._extract_fix_from_alternative(
                                tool, params, alt_result
                            )
                            if fixed_params:
                                params = fixed_params
                                break
        
        # 所有重试都失败
        return False, {"success": False, "error": last_error, "result": ""}
    
    def _update_context(self, result: dict):
        """更新执行上下文"""
        output = result.get("result", "")
        
        if output:
            self.execution_context["last_outputs"].append(output)
            
            # 保留最近10条输出
            if len(self.execution_context["last_outputs"]) > 10:
                self.execution_context["last_outputs"].pop(0)
            
            # 提取路径
            paths = self._extract_paths(output)
            self.execution_context["extracted_paths"].extend(paths)
            
            # 提取URL
            urls = self._extract_urls(output)
            self.execution_context["extracted_urls"].extend(urls)
    
    def _extract_paths(self, text: str) -> List[str]:
        """从文本中提取文件路径"""
        # 匹配绝对路径
        pattern = r'/[a-zA-Z0-9_/.-]+'
        paths = re.findall(pattern, text)
        
        # 过滤有效路径
        valid_paths = []
        for path in paths:
            # 排除太短的路径
            if len(path) > 5:
                valid_paths.append(path)
        
        return valid_paths
    
    def _extract_urls(self, text: str) -> List[str]:
        """从文本中提取URL"""
        pattern = r'https?://[^\s]+'
        return re.findall(pattern, text)
    
    def _try_auto_fix(
        self,
        tool: str,
        params: dict,
        error: str
    ) -> Optional[dict]:
        """尝试自动修复参数"""
        
        # 修复1：文件不存在 -> 查找最近提取的路径
        if "文件不存在" in error or "No such file" in error:
            if tool == "read_file":
                target_filename = os.path.basename(params.get("path", ""))
                
                # 在最近提取的路径中查找
                for path in reversed(self.execution_context["extracted_paths"]):
                    if target_filename in path or path.endswith(target_filename):
                        return {"path": path}
                    
                    # 尝试组合路径
                    if os.path.isdir(path):
                        combined = os.path.join(path, target_filename)
                        return {"path": combined}
        
        # 修复2：权限不足 -> 添加sudo
        if "权限不足" in error or "Permission denied" in error:
            if tool == "run_shell" and "sudo" not in params.get("command", ""):
                return {"command": f"sudo {params['command']}"}
        
        # 修复3：命令未找到 -> 尝试完整路径
        if "command not found" in error:
            if tool == "run_shell":
                cmd = params.get("command", "").split()[0]
                # 常见命令的完整路径
                common_paths = {
                    "python": "/usr/bin/python3",
                    "python3": "/usr/bin/python3",
                    "git": "/usr/bin/git",
                    "ls": "/bin/ls"
                }
                if cmd in common_paths:
                    new_cmd = params["command"].replace(cmd, common_paths[cmd], 1)
                    return {"command": new_cmd}
        
        return None
    
    def _generate_alternatives(
        self,
        tool: str,
        params: dict,
        error: str
    ) -> List[dict]:
        """生成替代方案"""
        alternatives = []
        
        # 替代方案1：文件不存在 -> 搜索文件
        if "文件不存在" in error or "No such file" in error:
            if tool == "read_file":
                path = params.get("path", "")
                filename = os.path.basename(path)
                dirname = os.path.dirname(path)
                
                # 方案A：在父目录搜索
                if dirname:
                    alternatives.append({
                        "tool": "run_shell",
                        "params": {"command": f"find {dirname} -name '{filename}' 2>/dev/null | head -5"}
                    })
                
                # 方案B：列出目录内容
                alternatives.append({
                    "tool": "run_shell",
                    "params": {"command": f"ls -la {dirname} 2>/dev/null"}
                })
                
                # 方案C：在常见位置搜索
                alternatives.append({
                    "tool": "run_shell",
                    "params": {"command": f"find /home/ubuntu -name '*{filename}*' 2>/dev/null | head -5"}
                })
        
        # 替代方案2：Git操作失败 -> 检查Git状态
        if "git" in error.lower() or tool == "run_shell" and "git" in params.get("command", ""):
            alternatives.append({
                "tool": "run_shell",
                "params": {"command": "git status 2>&1"}
            })
            alternatives.append({
                "tool": "run_shell",
                "params": {"command": "ls -la .git 2>&1"}
            })
        
        return alternatives
    
    def _extract_fix_from_alternative(
        self,
        original_tool: str,
        original_params: dict,
        alt_result: dict
    ) -> Optional[dict]:
        """从替代方案的结果中提取修复信息"""
        output = alt_result.get("result", "")
        
        # 如果是find命令的结果，提取找到的路径
        if "find" in output or "/" in output:
            paths = self._extract_paths(output)
            if paths and original_tool == "read_file":
                # 使用找到的第一个路径
                return {"path": paths[0]}
        
        # 如果是ls命令的结果，尝试组合路径
        if original_tool == "read_file":
            target_filename = os.path.basename(original_params.get("path", ""))
            lines = output.split("\n")
            
            for line in lines:
                if target_filename in line:
                    # 找到了文件，组合完整路径
                    dirname = os.path.dirname(original_params.get("path", ""))
                    return {"path": os.path.join(dirname, target_filename)}
        
        return None
    
    def get_context_summary(self) -> str:
        """获取执行上下文摘要"""
        summary = "### 执行上下文\n\n"
        
        if self.execution_context["extracted_paths"]:
            summary += "**提取的路径**:\n"
            for path in self.execution_context["extracted_paths"][-5:]:
                summary += f"- `{path}`\n"
            summary += "\n"
        
        if self.execution_context["extracted_urls"]:
            summary += "**提取的URL**:\n"
            for url in self.execution_context["extracted_urls"][-3:]:
                summary += f"- {url}\n"
            summary += "\n"
        
        if self.execution_context["last_outputs"]:
            summary += f"**最近输出**: {len(self.execution_context['last_outputs'])} 条\n"
        
        return summary


# 全局实例
_engine = None

def get_resilience_engine() -> ResilienceEngine:
    """获取全局韧性执行引擎实例"""
    global _engine
    if _engine is None:
        _engine = ResilienceEngine()
    return _engine


if __name__ == "__main__":
    # 测试代码
    engine = ResilienceEngine()
    
    # 测试路径提取
    output = "✅ 沙盒创建成功: /home/ubuntu/jarvis_evolution/v3.0_20260130_012151"
    engine._update_context({"result": output})
    
    print("提取的路径:", engine.execution_context["extracted_paths"])
    print("\n上下文摘要:")
    print(engine.get_context_summary())
