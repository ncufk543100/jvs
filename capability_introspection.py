"""
能力自省机制 (Capability Introspection)
让JARVIS清楚知道：我能做什么？我不能做什么？我需要什么工具？

核心功能：
1. 任务可行性评估
2. 能力边界识别
3. 工具需求分析
4. 替代方案生成
"""

import json
from typing import Dict, List, Optional, Tuple
from tool_registry import get_registry, ToolDefinition

class CapabilityIntrospection:
    """能力自省系统"""
    
    def __init__(self):
        self.registry = get_registry()
    
    def can_i_do_this(self, task: str) -> Dict:
        """
        评估：我能做这个任务吗？
        
        Args:
            task: 任务描述
        
        Returns:
            Dict: {
                can_do: bool,
                confidence: float,
                required_tools: List[str],
                missing_tools: List[str],
                alternative_approaches: List[str],
                reasoning: str
            }
        """
        # 1. 分析任务需要什么工具
        required_tools = self._analyze_required_tools(task)
        
        # 2. 检查哪些工具可用，哪些缺失
        available_tools = []
        missing_tools = []
        
        for tool_name in required_tools:
            if self.registry.get_tool(tool_name):
                available_tools.append(tool_name)
            else:
                missing_tools.append(tool_name)
        
        # 3. 评估可行性
        if not required_tools:
            # 没有明确的工具需求，可能是纯思考任务
            return {
                "can_do": True,
                "confidence": 0.8,
                "required_tools": [],
                "missing_tools": [],
                "alternative_approaches": [],
                "reasoning": "这是一个纯思考/分析任务，不需要特定工具"
            }
        
        if not missing_tools:
            # 所有工具都可用
            return {
                "can_do": True,
                "confidence": 0.9,
                "required_tools": available_tools,
                "missing_tools": [],
                "alternative_approaches": [],
                "reasoning": f"所需的 {len(available_tools)} 个工具都可用"
            }
        
        # 4. 有缺失工具，寻找替代方案
        alternatives = self._find_alternatives(missing_tools, task)
        
        if alternatives:
            return {
                "can_do": True,
                "confidence": 0.6,
                "required_tools": available_tools,
                "missing_tools": missing_tools,
                "alternative_approaches": alternatives,
                "reasoning": f"缺少 {len(missing_tools)} 个工具，但有 {len(alternatives)} 个替代方案"
            }
        else:
            return {
                "can_do": False,
                "confidence": 0.3,
                "required_tools": available_tools,
                "missing_tools": missing_tools,
                "alternative_approaches": [],
                "reasoning": f"缺少关键工具：{', '.join(missing_tools)}，且无替代方案"
            }
    
    def what_can_i_do(self) -> Dict:
        """
        列出我能做什么
        
        Returns:
            Dict: {
                categories: Dict[str, List[str]],
                total_capabilities: int,
                summary: str
            }
        """
        categories = {}
        
        for tool in self.registry.list_tools():
            if tool.category not in categories:
                categories[tool.category] = []
            
            categories[tool.category].append({
                "tool": tool.name,
                "description": tool.description,
                "efficiency": tool.efficiency_score
            })
        
        total = sum(len(tools) for tools in categories.values())
        
        summary = f"我当前拥有 {total} 个工具，覆盖 {len(categories)} 个类别：\n"
        for category, tools in categories.items():
            summary += f"- {category.upper()}: {len(tools)}个工具\n"
        
        return {
            "categories": categories,
            "total_capabilities": total,
            "summary": summary
        }
    
    def what_cant_i_do(self) -> List[str]:
        """
        列出我不能做什么（已知的限制）
        
        Returns:
            List[str]: 限制列表
        """
        limitations = [
            "无法直接访问网络（需要通过shell命令）",
            "无法生成图像或视频",
            "无法直接操作数据库（需要通过shell命令）",
            "无法执行需要GUI的操作",
            "无法访问用户的个人数据（除非明确授权）"
        ]
        
        # 从工具的限制中提取
        for tool in self.registry.list_tools():
            for limitation in tool.limitations:
                if limitation not in limitations:
                    limitations.append(f"{tool.name}: {limitation}")
        
        return limitations
    
    def do_i_need_new_tool(self, task: str) -> Dict:
        """
        判断：我需要创造新工具吗？
        
        Args:
            task: 任务描述
        
        Returns:
            Dict: {
                need_new_tool: bool,
                reason: str,
                suggested_tool_name: str,
                suggested_tool_description: str,
                can_use_existing: bool,
                existing_approach: str
            }
        """
        # 1. 检查现有工具是否足够
        recommendations = self.registry.recommend_tools_for_task(task)
        
        if recommendations:
            # 有推荐工具，评估效率
            best_tool = recommendations[0]
            
            if best_tool["score"] >= 1.0:
                # 现有工具效率足够
                return {
                    "need_new_tool": False,
                    "reason": f"现有工具 '{best_tool['tool'].name}' 效率足够（分数: {best_tool['score']:.1f}）",
                    "suggested_tool_name": None,
                    "suggested_tool_description": None,
                    "can_use_existing": True,
                    "existing_approach": f"使用 {best_tool['tool'].name}: {best_tool['tool'].description}"
                }
            else:
                # 现有工具效率较低
                return {
                    "need_new_tool": True,
                    "reason": f"现有工具效率较低（最高分数: {best_tool['score']:.1f}），建议创造专用工具",
                    "suggested_tool_name": self._suggest_tool_name(task),
                    "suggested_tool_description": f"专门用于: {task}",
                    "can_use_existing": True,
                    "existing_approach": f"备选方案: 使用 {best_tool['tool'].name}"
                }
        else:
            # 没有推荐工具
            # 检查是否可以用shell命令组合实现
            if self._can_use_shell_workaround(task):
                return {
                    "need_new_tool": False,
                    "reason": "可以通过组合shell命令实现",
                    "suggested_tool_name": None,
                    "suggested_tool_description": None,
                    "can_use_existing": True,
                    "existing_approach": "使用 run_shell 执行组合命令"
                }
            else:
                return {
                    "need_new_tool": True,
                    "reason": "没有合适的现有工具，且无法通过shell命令实现",
                    "suggested_tool_name": self._suggest_tool_name(task),
                    "suggested_tool_description": f"专门用于: {task}",
                    "can_use_existing": False,
                    "existing_approach": None
                }
    
    def _analyze_required_tools(self, task: str) -> List[str]:
        """
        分析任务需要什么工具
        
        简单的关键词匹配
        """
        task_lower = task.lower()
        required_tools = []
        
        # 文件操作
        if any(kw in task_lower for kw in ["创建文件", "写文件", "保存", "生成文件"]):
            required_tools.append("write_file")
        
        if any(kw in task_lower for kw in ["读取文件", "查看文件", "打开文件"]):
            required_tools.append("read_file")
        
        # Shell命令
        if any(kw in task_lower for kw in ["执行", "运行", "命令", "脚本"]):
            required_tools.append("run_shell")
        
        # 网络操作
        if any(kw in task_lower for kw in ["下载", "访问网页", "http", "api"]):
            required_tools.append("http_request")  # 这个工具可能不存在
        
        # 数据处理
        if any(kw in task_lower for kw in ["分析数据", "处理csv", "数据库"]):
            required_tools.append("data_processor")  # 这个工具可能不存在
        
        return required_tools
    
    def _find_alternatives(self, missing_tools: List[str], task: str) -> List[str]:
        """
        为缺失的工具寻找替代方案
        """
        alternatives = []
        
        for tool in missing_tools:
            if tool == "http_request":
                alternatives.append("使用 run_shell 执行 curl 或 wget 命令")
            elif tool == "data_processor":
                alternatives.append("使用 run_shell 执行 Python 脚本进行数据处理")
            elif "database" in tool.lower():
                alternatives.append("使用 run_shell 执行数据库命令行工具")
            else:
                # 通用替代方案
                alternatives.append(f"使用 run_shell 执行相关命令实现 {tool} 的功能")
        
        return alternatives
    
    def _can_use_shell_workaround(self, task: str) -> bool:
        """
        判断是否可以通过shell命令变通实现
        """
        # 大部分任务都可以通过shell命令实现
        # 除非是需要GUI或特殊硬件的任务
        task_lower = task.lower()
        
        cannot_use_shell = [
            "gui", "图形界面", "窗口", "鼠标", "点击",
            "摄像头", "麦克风", "硬件",
            "实时视频", "实时音频"
        ]
        
        for keyword in cannot_use_shell:
            if keyword in task_lower:
                return False
        
        return True
    
    def _suggest_tool_name(self, task: str) -> str:
        """
        根据任务建议工具名称
        """
        # 提取关键动词
        task_lower = task.lower()
        
        if "下载" in task_lower:
            return "download_file"
        elif "上传" in task_lower:
            return "upload_file"
        elif "分析" in task_lower:
            return "analyze_data"
        elif "转换" in task_lower:
            return "convert_format"
        elif "搜索" in task_lower:
            return "search_content"
        else:
            return "custom_tool"
    
    def generate_capability_report(self) -> str:
        """
        生成能力报告
        
        Returns:
            str: Markdown格式的能力报告
        """
        report = "# JARVIS 能力自省报告\n\n"
        
        # 1. 我能做什么
        capabilities = self.what_can_i_do()
        report += "## 我能做什么\n\n"
        report += capabilities["summary"] + "\n"
        
        for category, tools in capabilities["categories"].items():
            report += f"### {category.upper()}\n"
            for tool_info in tools:
                report += f"- **{tool_info['tool']}**: {tool_info['description']} (效率: {tool_info['efficiency']:.1f})\n"
            report += "\n"
        
        # 2. 我不能做什么
        limitations = self.what_cant_i_do()
        report += "## 我不能做什么（已知限制）\n\n"
        for limitation in limitations:
            report += f"- {limitation}\n"
        report += "\n"
        
        # 3. 工具统计
        report += "## 工具统计\n\n"
        report += f"- 总工具数：{capabilities['total_capabilities']}\n"
        report += f"- 工具类别数：{len(capabilities['categories'])}\n"
        
        return report


# 全局实例
_introspection = None

def get_introspection() -> CapabilityIntrospection:
    """获取全局能力自省实例"""
    global _introspection
    if _introspection is None:
        _introspection = CapabilityIntrospection()
    return _introspection


if __name__ == "__main__":
    # 测试代码
    intro = CapabilityIntrospection()
    
    print("=== 我能做这个任务吗？ ===")
    tasks = [
        "创建一个Python脚本文件",
        "下载一个网页的内容",
        "分析一个CSV文件",
        "思考如何优化代码"
    ]
    
    for task in tasks:
        result = intro.can_i_do_this(task)
        print(f"\n任务: {task}")
        print(f"能做: {result['can_do']}")
        print(f"置信度: {result['confidence']:.1%}")
        print(f"理由: {result['reasoning']}")
        if result['alternative_approaches']:
            print(f"替代方案: {result['alternative_approaches']}")
    
    print("\n\n=== 我需要创造新工具吗？ ===")
    for task in tasks:
        result = intro.do_i_need_new_tool(task)
        print(f"\n任务: {task}")
        print(f"需要新工具: {result['need_new_tool']}")
        print(f"理由: {result['reason']}")
    
    print("\n\n=== 能力报告 ===")
    print(intro.generate_capability_report())
