"""
工具创造决策系统 (Tool Creation Decision)
智能决策：何时应该创造新工具？

核心功能：
1. 评估创造新工具的必要性
2. 对比"使用现有工具"vs"创造新工具"的成本
3. 生成新工具的规格说明
4. 自动创造简单工具
"""

import json
import os
from typing import Dict, List, Optional
from tool_registry import get_registry, ToolDefinition
from capability_introspection import get_introspection
from external_tool_discovery import get_discovery

class ToolCreationDecision:
    """工具创造决策系统"""
    
    def __init__(self):
        self.registry = get_registry()
        self.introspection = get_introspection()
        self.discovery = get_discovery()
        
        # 成本阈值
        self.EFFICIENCY_THRESHOLD = 0.5  # 效率低于此值才考虑创造新工具
        self.COMPLEXITY_THRESHOLD = 3  # 复杂度高于此值才值得创造新工具
    
    def should_i_create_tool(self, task: str) -> Dict:
        """
        决策：我应该创造新工具吗？
        
        Args:
            task: 任务描述
        
        Returns:
            Dict: {
                should_create: bool,
                reason: str,
                cost_benefit_analysis: Dict,
                tool_spec: Dict,
                alternative: str
            }
        """
        # 1. 检查现有工具
        existing_tools = self.registry.recommend_tools_for_task(task)
        
        # 2. 检查外部工具
        external_tools = self.discovery.recommend_tool_for_task(task, max_results=1)
        
        # 3. 评估任务复杂度
        complexity = self._estimate_task_complexity(task)
        
        # 4. 成本效益分析
        cost_benefit = self._analyze_cost_benefit(
            task, existing_tools, external_tools, complexity
        )
        
        # 5. 做出决策
        should_create = cost_benefit["create_tool_score"] > cost_benefit["use_existing_score"]
        
        if should_create:
            # 生成工具规格
            tool_spec = self._generate_tool_spec(task)
            
            return {
                "should_create": True,
                "reason": cost_benefit["recommendation"],
                "cost_benefit_analysis": cost_benefit,
                "tool_spec": tool_spec,
                "alternative": cost_benefit["best_alternative"]
            }
        else:
            return {
                "should_create": False,
                "reason": cost_benefit["recommendation"],
                "cost_benefit_analysis": cost_benefit,
                "tool_spec": None,
                "alternative": cost_benefit["best_alternative"]
            }
    
    def create_tool_from_spec(self, tool_spec: Dict) -> Dict:
        """
        根据规格自动创造工具
        
        Args:
            tool_spec: 工具规格
        
        Returns:
            Dict: {success: bool, message: str, tool_path: str}
        """
        tool_name = tool_spec["name"]
        tool_path = f"/home/ubuntu/jarvis/{tool_name}.py"
        
        # 生成工具代码
        code = self._generate_tool_code(tool_spec)
        
        # 写入文件
        try:
            with open(tool_path, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # 注册到工具注册表
            tool_def = ToolDefinition(
                name=tool_name,
                description=tool_spec["description"],
                category=tool_spec["category"],
                parameters=tool_spec["parameters"],
                returns=tool_spec["returns"],
                examples=tool_spec.get("examples", []),
                efficiency_score=1.5,  # 新工具通常更高效
                limitations=[]
            )
            
            self.registry.register_tool(tool_def)
            
            return {
                "success": True,
                "message": f"成功创造工具 '{tool_name}'",
                "tool_path": tool_path
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"创造工具失败: {str(e)}",
                "tool_path": None
            }
    
    def _estimate_task_complexity(self, task: str) -> int:
        """
        估算任务复杂度（1-5）
        
        1: 非常简单（单步操作）
        2: 简单（2-3步操作）
        3: 中等（4-6步操作）
        4: 复杂（7-10步操作）
        5: 非常复杂（10+步操作）
        """
        task_lower = task.lower()
        
        # 关键词计数
        complexity_keywords = {
            "分析": 2,
            "处理": 2,
            "转换": 2,
            "生成": 2,
            "优化": 3,
            "集成": 3,
            "自动化": 3,
            "实时": 4,
            "并发": 4,
            "分布式": 5
        }
        
        score = 1
        for keyword, weight in complexity_keywords.items():
            if keyword in task_lower:
                score = max(score, weight)
        
        # 根据任务长度调整
        if len(task) > 100:
            score += 1
        
        return min(score, 5)
    
    def _analyze_cost_benefit(
        self,
        task: str,
        existing_tools: List[Dict],
        external_tools: List[Dict],
        complexity: int
    ) -> Dict:
        """
        成本效益分析
        
        Returns:
            Dict: {
                use_existing_score: float,
                create_tool_score: float,
                recommendation: str,
                best_alternative: str
            }
        """
        # 1. 使用现有工具的分数
        if existing_tools:
            best_existing = existing_tools[0]
            use_existing_score = best_existing["score"] * 0.8  # 现有工具有学习成本
        else:
            use_existing_score = 0.0
        
        # 2. 使用外部工具的分数
        if external_tools:
            best_external = external_tools[0]
            use_external_score = best_external["evaluation"]["confidence"] * 0.6  # 外部工具集成成本高
        else:
            use_external_score = 0.0
        
        # 3. 创造新工具的分数
        # 基础分数：复杂度越高，越值得创造专用工具
        create_tool_score = complexity * 0.2
        
        # 如果现有工具效率低，提高创造新工具的分数
        if use_existing_score < self.EFFICIENCY_THRESHOLD:
            create_tool_score += 0.3
        
        # 如果是重复性任务，提高创造新工具的分数
        if any(kw in task.lower() for kw in ["自动化", "批量", "定期", "重复"]):
            create_tool_score += 0.4
        
        # 4. 生成推荐
        scores = {
            "use_existing": use_existing_score,
            "use_external": use_external_score,
            "create_tool": create_tool_score
        }
        
        best_option = max(scores, key=scores.get)
        
        if best_option == "create_tool":
            recommendation = f"建议创造新工具（分数: {create_tool_score:.2f}），因为现有方案效率较低且任务复杂度为 {complexity}"
            best_alternative = None
        elif best_option == "use_existing":
            recommendation = f"建议使用现有工具 '{existing_tools[0]['tool'].name}'（分数: {use_existing_score:.2f}）"
            best_alternative = f"使用 {existing_tools[0]['tool'].name}"
        else:
            recommendation = f"建议集成外部工具 '{external_tools[0]['tool_info']['name']}'（分数: {use_external_score:.2f}）"
            best_alternative = f"集成 {external_tools[0]['tool_info']['name']}"
        
        return {
            "use_existing_score": use_existing_score,
            "use_external_score": use_external_score,
            "create_tool_score": create_tool_score,
            "recommendation": recommendation,
            "best_alternative": best_alternative
        }
    
    def _generate_tool_spec(self, task: str) -> Dict:
        """
        生成工具规格
        
        Args:
            task: 任务描述
        
        Returns:
            Dict: 工具规格
        """
        # 从任务中提取关键信息
        task_lower = task.lower()
        
        # 确定工具名称
        if "下载" in task_lower:
            name = "download_tool"
            category = "network"
        elif "上传" in task_lower:
            name = "upload_tool"
            category = "network"
        elif "分析" in task_lower:
            name = "analyze_tool"
            category = "analysis"
        elif "转换" in task_lower:
            name = "convert_tool"
            category = "conversion"
        elif "生成" in task_lower:
            name = "generate_tool"
            category = "generation"
        else:
            name = "custom_tool"
            category = "utility"
        
        return {
            "name": name,
            "description": f"专门用于: {task}",
            "category": category,
            "parameters": {
                "input": {
                    "type": "string",
                    "required": True,
                    "description": "输入数据"
                }
            },
            "returns": "处理结果",
            "examples": [
                f'{{"input": "示例输入"}}'
            ]
        }
    
    def _generate_tool_code(self, tool_spec: Dict) -> str:
        """
        生成工具代码
        
        Args:
            tool_spec: 工具规格
        
        Returns:
            str: Python代码
        """
        code = f'''"""
{tool_spec["name"]} - {tool_spec["description"]}
自动生成的工具
"""

def {tool_spec["name"]}(**params):
    """
    {tool_spec["description"]}
    
    参数:
'''
        
        for param_name, param_info in tool_spec["parameters"].items():
            code += f'        {param_name} ({param_info["type"]}): {param_info["description"]}\n'
        
        code += f'''    
    返回:
        {tool_spec["returns"]}
    """
    # TODO: 实现工具逻辑
    result = params.get("input", "")
    
    return {{
        "success": True,
        "result": result
    }}


if __name__ == "__main__":
    # 测试代码
    result = {tool_spec["name"]}(input="测试输入")
    print(result)
'''
        
        return code


# 全局实例
_decision = None

def get_decision() -> ToolCreationDecision:
    """获取全局工具创造决策实例"""
    global _decision
    if _decision is None:
        _decision = ToolCreationDecision()
    return _decision


if __name__ == "__main__":
    # 测试代码
    decision = ToolCreationDecision()
    
    print("=== 工具创造决策测试 ===\n")
    
    tasks = [
        "创建一个Python文件",
        "下载并分析100个网页的内容",
        "自动化生成每日报告",
        "批量转换图片格式"
    ]
    
    for task in tasks:
        print(f"任务: {task}")
        result = decision.should_i_create_tool(task)
        
        print(f"应该创造工具: {result['should_create']}")
        print(f"理由: {result['reason']}")
        
        if result['tool_spec']:
            print(f"工具规格: {result['tool_spec']['name']} - {result['tool_spec']['description']}")
        
        if result['alternative']:
            print(f"替代方案: {result['alternative']}")
        
        print("\n" + "="*60 + "\n")
