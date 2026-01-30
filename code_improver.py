"""
自动改进方案生成和代码修改系统
基于分析结果自动生成改进方案并修改代码
"""

import os
import json
import re
from typing import Dict, List
from datetime import datetime
import sys

sys.path.append(os.path.dirname(__file__))
from llm import chat

class CodeImprover:
    """代码改进器"""
    
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.improvement_history = []
    
    def generate_improvement_plan(
        self,
        goal: str,
        analysis: Dict
    ) -> List[Dict]:
        """
        根据分析结果生成改进方案
        
        Args:
            goal: 进化目标
            analysis: 代码分析结果
        
        Returns:
            List[Dict]: 改进方案列表
        """
        print(f"\n💡 生成改进方案...")
        
        prompt = f"""
你是JARVIS的自我进化引擎。根据代码分析结果，生成具体的改进方案。

**进化目标**: {goal}

**代码分析结果**:
- 总体评估: {analysis.get('summary', 'N/A')}
- 优势: {', '.join(analysis.get('strengths', [])[:3])}
- 不足: {', '.join(analysis.get('weaknesses', [])[:3])}
- 改进机会: {', '.join(analysis.get('opportunities', [])[:3])}

**优先改进领域**:
{json.dumps(analysis.get('priority_areas', []), indent=2, ensure_ascii=False)}

请生成3-5个具体的改进方案，每个方案包含：
1. 目标文件
2. 改进描述
3. 具体的代码修改
4. 预期效果

以JSON格式返回：
[
    {{
        "file": "文件名.py",
        "description": "改进描述",
        "changes": [
            {{
                "type": "add/modify/delete",
                "location": "函数名或行号",
                "old_code": "原代码（如果是modify）",
                "new_code": "新代码",
                "reason": "修改原因"
            }},
            ...
        ],
        "expected_impact": "预期效果"
    }},
    ...
]
"""
        
        response = chat(prompt)
        
        # 解析JSON响应
        try:
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                improvements = json.loads(json_match.group(0))
            else:
                # 如果没有JSON，返回空列表
                improvements = []
        except Exception as e:
            print(f"   ⚠️  解析失败: {e}")
            improvements = []
        
        print(f"   ✅ 生成了 {len(improvements)} 个改进方案")
        return improvements
    
    def apply_improvements(
        self,
        improvements: List[Dict],
        dry_run: bool = False
    ) -> Dict:
        """
        应用改进方案
        
        Args:
            improvements: 改进方案列表
            dry_run: 是否只是模拟（不实际修改文件）
        
        Returns:
            Dict: {
                applied: List[str],  # 成功应用的文件
                failed: List[Dict],  # 失败的改进
                backup_path: str  # 备份路径
            }
        """
        print(f"\n🔧 应用改进方案...")
        if dry_run:
            print("   （模拟模式，不实际修改文件）")
        
        applied = []
        failed = []
        
        # 创建备份
        backup_path = None
        if not dry_run:
            backup_path = self._create_backup()
        
        for improvement in improvements:
            file_name = improvement.get("file")
            file_path = os.path.join(self.project_path, file_name)
            
            if not os.path.exists(file_path):
                failed.append({
                    "file": file_name,
                    "error": "文件不存在"
                })
                continue
            
            try:
                # 读取文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 应用所有修改
                modified_content = content
                for change in improvement.get("changes", []):
                    modified_content = self._apply_single_change(
                        modified_content,
                        change
                    )
                
                # 写回文件
                if not dry_run:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(modified_content)
                
                applied.append(file_name)
                print(f"   ✅ {file_name}")
                
            except Exception as e:
                failed.append({
                    "file": file_name,
                    "error": str(e)
                })
                print(f"   ❌ {file_name}: {e}")
        
        return {
            "applied": applied,
            "failed": failed,
            "backup_path": backup_path
        }
    
    def _apply_single_change(self, content: str, change: Dict) -> str:
        """应用单个修改"""
        change_type = change.get("type")
        
        if change_type == "add":
            # 添加代码
            new_code = change.get("new_code", "")
            location = change.get("location", "end")
            
            if location == "end":
                return content + "\n" + new_code
            else:
                # 在指定位置插入
                return content  # 简化实现
        
        elif change_type == "modify":
            # 修改代码
            old_code = change.get("old_code", "")
            new_code = change.get("new_code", "")
            
            if old_code and old_code in content:
                return content.replace(old_code, new_code, 1)
            else:
                return content
        
        elif change_type == "delete":
            # 删除代码
            old_code = change.get("old_code", "")
            
            if old_code and old_code in content:
                return content.replace(old_code, "", 1)
            else:
                return content
        
        return content
    
    def _create_backup(self) -> str:
        """创建备份"""
        import shutil
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.project_path}_backup_{timestamp}"
        
        shutil.copytree(
            self.project_path,
            backup_path,
            ignore=shutil.ignore_patterns(
                '__pycache__',
                '*.pyc',
                '.git',
                'data',
                'logs',
                '*_backup_*'
            )
        )
        
        print(f"   📦 已备份到: {backup_path}")
        return backup_path
    
    def generate_code_fix(
        self,
        file_path: str,
        issue_description: str
    ) -> str:
        """
        为特定问题生成代码修复
        
        Args:
            file_path: 文件路径
            issue_description: 问题描述
        
        Returns:
            str: 修复后的代码
        """
        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        prompt = f"""
请修复以下代码中的问题。

**文件**: {os.path.basename(file_path)}
**问题**: {issue_description}

**原代码**:
```python
{content[:2000]}  # 限制长度
```

请提供修复后的完整代码。
"""
        
        response = chat(prompt)
        
        # 提取代码块
        code_match = re.search(r'```python\n([\s\S]*?)\n```', response)
        if code_match:
            return code_match.group(1)
        else:
            return content  # 如果提取失败，返回原代码


if __name__ == "__main__":
    # 测试代码
    improver = CodeImprover("/home/ubuntu/jarvis")
    
    print("=== 代码改进器测试 ===\n")
    
    # 模拟分析结果
    analysis = {
        "summary": "代码质量良好，但缺少某些高级功能",
        "strengths": ["模块化设计", "清晰的架构"],
        "weaknesses": ["缺少自动测试", "错误处理不完善"],
        "opportunities": ["添加单元测试", "改进错误处理"],
        "priority_areas": [
            {
                "area": "错误处理",
                "reason": "提高系统稳定性",
                "impact": "减少崩溃",
                "effort": "medium"
            }
        ]
    }
    
    # 生成改进方案
    improvements = improver.generate_improvement_plan(
        "提高代码质量和稳定性",
        analysis
    )
    
    print(f"\n生成了 {len(improvements)} 个改进方案")
    for i, imp in enumerate(improvements, 1):
        print(f"\n改进 {i}:")
        print(f"  文件: {imp.get('file', 'N/A')}")
        print(f"  描述: {imp.get('description', 'N/A')}")
        print(f"  修改数: {len(imp.get('changes', []))}")
        print(f"  预期效果: {imp.get('expected_impact', 'N/A')}")
    
    # 模拟应用（dry run）
    if improvements:
        print("\n" + "="*50)
        result = improver.apply_improvements(improvements, dry_run=True)
        print(f"\n模拟应用结果:")
        print(f"  成功: {len(result['applied'])} 个文件")
        print(f"  失败: {len(result['failed'])} 个文件")
