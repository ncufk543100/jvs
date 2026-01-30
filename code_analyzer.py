"""
LLM驱动的代码分析系统
用于自动分析JARVIS代码库，识别改进机会
"""

import os
import json
from typing import Dict, List
from pathlib import Path
import sys

# 导入LLM
sys.path.append(os.path.dirname(__file__))
from llm import chat

class CodeAnalyzer:
    """代码分析器"""
    
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.analysis_cache = {}
    
    def analyze_project(self, goal: str) -> Dict:
        """
        分析整个项目
        
        Args:
            goal: 进化目标
        
        Returns:
            Dict: {
                summary: str,  # 总体评估
                strengths: List[str],  # 优势
                weaknesses: List[str],  # 不足
                opportunities: List[str],  # 改进机会
                priority_areas: List[Dict]  # 优先改进领域
            }
        """
        print(f"\n📊 分析项目结构...")
        
        # 1. 获取项目结构
        structure = self._get_project_structure()
        
        # 2. 读取关键文件
        key_files = self._read_key_files()
        
        # 3. 使用LLM分析
        prompt = f"""
你是一个资深的软件架构师和代码审查专家。请分析JARVIS项目的当前状态。

**进化目标**: {goal}

**项目结构**:
{json.dumps(structure, indent=2, ensure_ascii=False)}

**关键文件内容**:
{self._format_file_contents(key_files)}

请从以下角度进行分析：
1. **总体评估**: 当前代码质量、架构合理性
2. **优势**: 已经做得好的地方
3. **不足**: 存在的问题和缺陷
4. **改进机会**: 为了达成目标，可以改进的地方
5. **优先级**: 哪些改进最重要、最紧急

请以JSON格式返回分析结果：
{{
    "summary": "总体评估...",
    "strengths": ["优势1", "优势2", ...],
    "weaknesses": ["不足1", "不足2", ...],
    "opportunities": ["机会1", "机会2", ...],
    "priority_areas": [
        {{
            "area": "领域名称",
            "reason": "为什么重要",
            "impact": "预期影响",
            "effort": "所需工作量(low/medium/high)"
        }},
        ...
    ]
}}
"""
        
        response = chat(prompt)
        
        # 解析JSON响应
        try:
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                analysis = json.loads(json_match.group(0))
            else:
                # 如果没有JSON，返回默认结构
                analysis = {
                    "summary": response[:200],
                    "strengths": [],
                    "weaknesses": [],
                    "opportunities": [],
                    "priority_areas": []
                }
        except:
            analysis = {
                "summary": "分析失败",
                "strengths": [],
                "weaknesses": [],
                "opportunities": [],
                "priority_areas": []
            }
        
        return analysis
    
    def analyze_file(self, file_path: str, context: str = "") -> Dict:
        """
        分析单个文件
        
        Args:
            file_path: 文件路径
            context: 上下文信息
        
        Returns:
            Dict: {
                quality_score: float,  # 质量评分 (0-10)
                issues: List[Dict],  # 问题列表
                suggestions: List[Dict]  # 改进建议
            }
        """
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用LLM分析
        prompt = f"""
分析以下Python文件，识别问题和改进机会。

**文件**: {os.path.basename(file_path)}
**上下文**: {context}

**代码**:
```python
{content[:3000]}  # 限制长度
```

请评估：
1. 代码质量 (0-10分)
2. 存在的问题
3. 改进建议

以JSON格式返回：
{{
    "quality_score": 7.5,
    "issues": [
        {{"type": "bug/style/performance", "line": 10, "description": "问题描述"}},
        ...
    ],
    "suggestions": [
        {{"priority": "high/medium/low", "description": "建议描述", "benefit": "预期收益"}},
        ...
    ]
}}
"""
        
        response = chat(prompt)
        
        # 解析响应
        try:
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                analysis = json.loads(json_match.group(0))
            else:
                analysis = {
                    "quality_score": 7.0,
                    "issues": [],
                    "suggestions": []
                }
        except:
            analysis = {
                "quality_score": 7.0,
                "issues": [],
                "suggestions": []
            }
        
        return analysis
    
    def _get_project_structure(self) -> Dict:
        """获取项目结构"""
        structure = {
            "total_files": 0,
            "total_lines": 0,
            "modules": []
        }
        
        for py_file in Path(self.project_path).glob("*.py"):
            with open(py_file, 'r', encoding='utf-8') as f:
                lines = len(f.readlines())
            
            structure["modules"].append({
                "name": py_file.name,
                "lines": lines
            })
            structure["total_files"] += 1
            structure["total_lines"] += lines
        
        return structure
    
    def _read_key_files(self) -> Dict[str, str]:
        """读取关键文件"""
        key_files = {}
        important_files = [
            "agent_final.py",
            "planner.py",
            "executor.py",
            "llm.py",
            "server.py"
        ]
        
        for filename in important_files:
            file_path = os.path.join(self.project_path, filename)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    # 只读取前50行
                    lines = f.readlines()[:50]
                    key_files[filename] = ''.join(lines)
        
        return key_files
    
    def _format_file_contents(self, files: Dict[str, str]) -> str:
        """格式化文件内容"""
        formatted = []
        for filename, content in files.items():
            formatted.append(f"### {filename}\n```python\n{content}\n```\n")
        return '\n'.join(formatted)


if __name__ == "__main__":
    # 测试代码
    analyzer = CodeAnalyzer("/home/ubuntu/jarvis")
    
    print("=== LLM驱动的代码分析系统测试 ===\n")
    
    # 分析项目
    analysis = analyzer.analyze_project("在用户可感知的功能与行为层面，全面超越Manus")
    
    print("\n📊 分析结果：")
    print(f"\n总体评估: {analysis['summary']}")
    print(f"\n优势 ({len(analysis['strengths'])}):")
    for s in analysis['strengths'][:3]:
        print(f"  ✅ {s}")
    
    print(f"\n不足 ({len(analysis['weaknesses'])}):")
    for w in analysis['weaknesses'][:3]:
        print(f"  ⚠️ {w}")
    
    print(f"\n改进机会 ({len(analysis['opportunities'])}):")
    for o in analysis['opportunities'][:3]:
        print(f"  💡 {o}")
    
    print(f"\n优先改进领域 ({len(analysis['priority_areas'])}):")
    for area in analysis['priority_areas'][:3]:
        print(f"  🎯 {area.get('area', 'N/A')} - {area.get('reason', 'N/A')}")
