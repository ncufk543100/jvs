"""
工具清单和注册系统 (Tool Registry)
JARVIS 工具管理核心 - 让JARVIS清楚知道自己有什么工具

核心功能：
1. 工具注册和管理
2. 工具能力描述
3. 工具使用示例
4. 工具效率评估
"""

import json
import os
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict

@dataclass
class ToolDefinition:
    """工具定义"""
    name: str
    description: str
    category: str  # file, shell, network, analysis, generation, etc.
    parameters: Dict[str, Dict]  # {param_name: {type, required, description}}
    returns: str
    examples: List[str]
    efficiency_score: float = 1.0  # 效率分数（1.0=标准，>1.0=高效，<1.0=低效）
    limitations: List[str] = None
    
    def __post_init__(self):
        if self.limitations is None:
            self.limitations = []
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ToolDefinition':
        return cls(**data)


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self, data_dir: str = "/home/ubuntu/jarvis/data"):
        self.data_dir = data_dir
        self.registry_file = os.path.join(data_dir, "tool_registry.json")
        
        os.makedirs(data_dir, exist_ok=True)
        
        # 工具注册表
        self.tools: Dict[str, ToolDefinition] = {}
        
        # 工具执行函数映射
        self.tool_functions: Dict[str, Callable] = {}
        
        # 加载注册表
        self._load_registry()
        
        # 注册内置工具
        self._register_builtin_tools()
    
    def register_tool(
        self,
        tool_def: ToolDefinition,
        function: Callable = None
    ) -> None:
        """
        注册工具
        
        Args:
            tool_def: 工具定义
            function: 工具执行函数（可选）
        """
        self.tools[tool_def.name] = tool_def
        
        if function:
            self.tool_functions[tool_def.name] = function
        
        self._save_registry()
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """获取工具定义"""
        return self.tools.get(name)
    
    def list_tools(self, category: str = None) -> List[ToolDefinition]:
        """
        列出工具
        
        Args:
            category: 工具分类（可选）
        
        Returns:
            List[ToolDefinition]: 工具列表
        """
        tools = list(self.tools.values())
        
        if category:
            tools = [t for t in tools if t.category == category]
        
        return tools
    
    def search_tools(self, query: str) -> List[ToolDefinition]:
        """
        搜索工具
        
        Args:
            query: 搜索关键词
        
        Returns:
            List[ToolDefinition]: 匹配的工具列表
        """
        query_lower = query.lower()
        results = []
        
        for tool in self.tools.values():
            # 搜索名称和描述
            if (query_lower in tool.name.lower() or 
                query_lower in tool.description.lower()):
                results.append(tool)
        
        return results
    
    def get_tool_summary(self) -> str:
        """
        获取工具摘要
        
        Returns:
            str: Markdown格式的工具摘要
        """
        summary = "# JARVIS 工具清单\n\n"
        
        # 按分类组织
        categories = {}
        for tool in self.tools.values():
            if tool.category not in categories:
                categories[tool.category] = []
            categories[tool.category].append(tool)
        
        for category, tools in sorted(categories.items()):
            summary += f"## {category.upper()}\n\n"
            
            for tool in sorted(tools, key=lambda t: t.name):
                summary += f"### `{tool.name}`\n"
                summary += f"**描述**: {tool.description}\n\n"
                summary += f"**效率分数**: {tool.efficiency_score:.1f}\n\n"
                
                if tool.limitations:
                    summary += f"**限制**: {', '.join(tool.limitations)}\n\n"
                
                summary += "**参数**:\n"
                for param_name, param_info in tool.parameters.items():
                    required = "必需" if param_info.get("required") else "可选"
                    summary += f"- `{param_name}` ({param_info['type']}, {required}): {param_info['description']}\n"
                
                summary += f"\n**返回**: {tool.returns}\n\n"
                
                if tool.examples:
                    summary += "**示例**:\n"
                    for example in tool.examples:
                        summary += f"```json\n{example}\n```\n"
                
                summary += "\n---\n\n"
        
        return summary
    
    def evaluate_tool_for_task(self, task: str, tool_name: str) -> Dict:
        """
        评估工具对任务的适用性
        
        Args:
            task: 任务描述
            tool_name: 工具名称
        
        Returns:
            Dict: {suitable: bool, reason: str, efficiency: float}
        """
        tool = self.get_tool(tool_name)
        
        if not tool:
            return {
                "suitable": False,
                "reason": "工具不存在",
                "efficiency": 0.0
            }
        
        # 简单的关键词匹配
        task_lower = task.lower()
        tool_keywords = tool.name.lower().split('_') + tool.description.lower().split()
        
        matches = sum(1 for kw in tool_keywords if kw in task_lower)
        
        if matches > 0:
            return {
                "suitable": True,
                "reason": f"工具与任务匹配（{matches}个关键词）",
                "efficiency": tool.efficiency_score
            }
        else:
            return {
                "suitable": False,
                "reason": "工具与任务不匹配",
                "efficiency": 0.0
            }
    
    def recommend_tools_for_task(self, task: str, top_k: int = 3) -> List[Dict]:
        """
        为任务推荐工具
        
        Args:
            task: 任务描述
            top_k: 返回前K个推荐
        
        Returns:
            List[Dict]: [{tool: ToolDefinition, score: float, reason: str}]
        """
        recommendations = []
        
        for tool in self.tools.values():
            eval_result = self.evaluate_tool_for_task(task, tool.name)
            
            if eval_result["suitable"]:
                recommendations.append({
                    "tool": tool,
                    "score": eval_result["efficiency"],
                    "reason": eval_result["reason"]
                })
        
        # 按分数排序
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        
        return recommendations[:top_k]
    
    def _register_builtin_tools(self) -> None:
        """注册内置工具"""
        
        # 1. write_file
        self.register_tool(ToolDefinition(
            name="write_file",
            description="写入文件内容（覆盖模式）",
            category="file",
            parameters={
                "path": {
                    "type": "string",
                    "required": True,
                    "description": "文件路径（写入时必须在 /home/ubuntu/jarvis/ 目录内）"
                },
                "content": {
                    "type": "string",
                    "required": True,
                    "description": "文件内容"
                }
            },
            returns="执行结果 {success: bool, message: str}",
            examples=[
                '{"path": "/home/ubuntu/jarvis/test.py", "content": "print(\\"Hello\\")"}',
                '{"path": "/home/ubuntu/jarvis/data.txt", "content": "Some data"}'
            ],
            efficiency_score=1.0,
            limitations=["只能写入项目目录内的文件", "会覆盖现有文件"]
        ))
        
        # 2. read_file
        self.register_tool(ToolDefinition(
            name="read_file",
            description="读取文件内容",
            category="file",
            parameters={
                "path": {
                    "type": "string",
                    "required": True,
                    "description": "文件路径（可以读取系统任意位置的文件）"
                }
            },
            returns="文件内容或错误信息",
            examples=[
                '{"path": "/home/ubuntu/jarvis/test.py"}',
                '{"path": "/etc/hostname"}',
                '{"path": "~/.bashrc"}'
            ],
            efficiency_score=1.0,
            limitations=["需要文件读取权限"]
        ))
        
        # 3. run_shell
        self.register_tool(ToolDefinition(
            name="run_shell",
            description="执行Shell命令",
            category="shell",
            parameters={
                "command": {
                    "type": "string",
                    "required": True,
                    "description": "要执行的Shell命令"
                }
            },
            returns="命令输出或错误信息",
            examples=[
                '{"command": "python3 test.py"}',
                '{"command": "ls -la"}',
                '{"command": "cat file.txt | grep error"}'
            ],
            efficiency_score=1.2,  # Shell命令通常很高效
            limitations=["需要命令执行权限", "某些命令可能需要sudo"]
        ))
    
    def _load_registry(self) -> None:
        """加载工具注册表"""
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    for tool_data in data.get("tools", []):
                        tool = ToolDefinition.from_dict(tool_data)
                        self.tools[tool.name] = tool
            except:
                pass
    
    def _save_registry(self) -> None:
        """保存工具注册表"""
        data = {
            "tools": [tool.to_dict() for tool in self.tools.values()]
        }
        
        with open(self.registry_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


# 全局实例
_registry = None

def get_registry() -> ToolRegistry:
    """获取全局工具注册表实例"""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


if __name__ == "__main__":
    # 测试代码
    registry = ToolRegistry()
    
    print("=== 工具清单 ===")
    print(f"总工具数: {len(registry.tools)}")
    
    print("\n=== 搜索文件相关工具 ===")
    file_tools = registry.search_tools("文件")
    for tool in file_tools:
        print(f"- {tool.name}: {tool.description}")
    
    print("\n=== 为任务推荐工具 ===")
    task = "创建一个Python脚本文件"
    recommendations = registry.recommend_tools_for_task(task)
    for rec in recommendations:
        print(f"- {rec['tool'].name} (分数: {rec['score']:.1f}): {rec['reason']}")
    
    print("\n=== 工具摘要（前50行）===")
    summary = registry.get_tool_summary()
    print('\n'.join(summary.split('\n')[:50]))
