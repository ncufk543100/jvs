"""
外部工具发现和集成 (External Tool Discovery)
从GitHub等平台发现和集成开源skill/工具

核心功能：
1. 搜索GitHub上的开源skill
2. 评估外部工具的适用性
3. 下载和集成外部工具
4. 管理外部工具库
"""

import json
import os
import subprocess
from typing import Dict, List, Optional
from tool_registry import get_registry, ToolDefinition

class ExternalToolDiscovery:
    """外部工具发现系统"""
    
    def __init__(self, tools_dir: str = "/home/ubuntu/jarvis/external_tools"):
        self.tools_dir = tools_dir
        self.registry = get_registry()
        self.index_file = os.path.join(tools_dir, "external_tools_index.json")
        
        os.makedirs(tools_dir, exist_ok=True)
        
        # 外部工具索引
        self.external_tools = self._load_index()
    
    def search_github_skills(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        搜索GitHub上的开源skill
        
        Args:
            query: 搜索关键词
            max_results: 最多返回结果数
        
        Returns:
            List[Dict]: [{name, description, url, stars, language}]
        """
        # 使用gh CLI搜索GitHub
        try:
            cmd = f'gh search repos "{query} skill OR tool" --limit {max_results} --json name,description,url,stargazersCount,primaryLanguage'
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                repos = json.loads(result.stdout)
                return [
                    {
                        "name": repo["name"],
                        "description": repo.get("description", ""),
                        "url": repo["url"],
                        "stars": repo.get("stargazersCount", 0),
                        "language": repo.get("primaryLanguage", {}).get("name", "Unknown")
                    }
                    for repo in repos
                ]
            else:
                # gh CLI不可用，返回预定义的工具列表
                return self._get_known_tools(query)
        except:
            return self._get_known_tools(query)
    
    def _get_known_tools(self, query: str) -> List[Dict]:
        """
        返回已知的优质工具列表
        
        当GitHub API不可用时的备选方案
        """
        known_tools = [
            {
                "name": "manus-skills",
                "description": "Manus官方技能库，包含Excel生成、PPT制作等高质量skill",
                "url": "https://github.com/manus-ai/skills",
                "stars": 1000,
                "language": "Python",
                "category": "productivity"
            },
            {
                "name": "langchain-tools",
                "description": "LangChain工具集，包含大量AI工具",
                "url": "https://github.com/langchain-ai/langchain",
                "stars": 50000,
                "language": "Python",
                "category": "ai"
            },
            {
                "name": "autogen-skills",
                "description": "Microsoft AutoGen技能库",
                "url": "https://github.com/microsoft/autogen",
                "stars": 20000,
                "language": "Python",
                "category": "ai"
            }
        ]
        
        # 简单的关键词匹配
        query_lower = query.lower()
        return [
            tool for tool in known_tools
            if query_lower in tool["name"].lower() or
               query_lower in tool["description"].lower()
        ]
    
    def evaluate_external_tool(self, tool_info: Dict, task: str) -> Dict:
        """
        评估外部工具对任务的适用性
        
        Args:
            tool_info: 工具信息
            task: 任务描述
        
        Returns:
            Dict: {
                suitable: bool,
                confidence: float,
                reason: str,
                integration_difficulty: str  # easy, medium, hard
            }
        """
        task_lower = task.lower()
        tool_name = tool_info["name"].lower()
        tool_desc = tool_info.get("description", "").lower()
        
        # 计算相关性分数
        relevance_score = 0.0
        
        # 名称匹配
        if any(word in tool_name for word in task_lower.split()):
            relevance_score += 0.3
        
        # 描述匹配
        if any(word in tool_desc for word in task_lower.split()):
            relevance_score += 0.3
        
        # 语言匹配（Python工具更容易集成）
        if tool_info.get("language") == "Python":
            relevance_score += 0.2
        
        # 星标数（流行度）
        stars = tool_info.get("stars", 0)
        if stars > 1000:
            relevance_score += 0.2
        elif stars > 100:
            relevance_score += 0.1
        
        # 评估集成难度
        if tool_info.get("language") == "Python":
            integration_difficulty = "easy"
        elif tool_info.get("language") in ["JavaScript", "TypeScript"]:
            integration_difficulty = "medium"
        else:
            integration_difficulty = "hard"
        
        # 判断是否适用
        suitable = relevance_score >= 0.4
        
        return {
            "suitable": suitable,
            "confidence": min(relevance_score, 1.0),
            "reason": f"相关性分数: {relevance_score:.2f}, 语言: {tool_info.get('language')}, 星标: {stars}",
            "integration_difficulty": integration_difficulty
        }
    
    def integrate_tool(self, tool_info: Dict) -> Dict:
        """
        集成外部工具
        
        Args:
            tool_info: 工具信息
        
        Returns:
            Dict: {success: bool, message: str, tool_path: str}
        """
        tool_name = tool_info["name"]
        tool_url = tool_info["url"]
        tool_path = os.path.join(self.tools_dir, tool_name)
        
        # 检查是否已存在
        if os.path.exists(tool_path):
            return {
                "success": False,
                "message": f"工具 '{tool_name}' 已存在",
                "tool_path": tool_path
            }
        
        # 克隆仓库
        try:
            cmd = f"git clone {tool_url} {tool_path}"
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                # 添加到索引
                self.external_tools[tool_name] = {
                    **tool_info,
                    "path": tool_path,
                    "integrated_at": __import__("datetime").datetime.now().isoformat()
                }
                self._save_index()
                
                return {
                    "success": True,
                    "message": f"成功集成工具 '{tool_name}'",
                    "tool_path": tool_path
                }
            else:
                return {
                    "success": False,
                    "message": f"克隆失败: {result.stderr}",
                    "tool_path": None
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"集成失败: {str(e)}",
                "tool_path": None
            }
    
    def list_integrated_tools(self) -> List[Dict]:
        """列出已集成的外部工具"""
        return list(self.external_tools.values())
    
    def recommend_tool_for_task(self, task: str, max_results: int = 3) -> List[Dict]:
        """
        为任务推荐外部工具
        
        Args:
            task: 任务描述
            max_results: 最多返回结果数
        
        Returns:
            List[Dict]: [{tool_info, evaluation}]
        """
        # 1. 搜索相关工具
        search_results = self.search_github_skills(task, max_results=10)
        
        # 2. 评估每个工具
        recommendations = []
        for tool_info in search_results:
            evaluation = self.evaluate_external_tool(tool_info, task)
            
            if evaluation["suitable"]:
                recommendations.append({
                    "tool_info": tool_info,
                    "evaluation": evaluation
                })
        
        # 3. 按置信度排序
        recommendations.sort(
            key=lambda x: x["evaluation"]["confidence"],
            reverse=True
        )
        
        return recommendations[:max_results]
    
    def _load_index(self) -> Dict:
        """加载外部工具索引"""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_index(self) -> None:
        """保存外部工具索引"""
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.external_tools, f, ensure_ascii=False, indent=2)


# 全局实例
_discovery = None

def get_discovery() -> ExternalToolDiscovery:
    """获取全局外部工具发现实例"""
    global _discovery
    if _discovery is None:
        _discovery = ExternalToolDiscovery()
    return _discovery


if __name__ == "__main__":
    # 测试代码
    discovery = ExternalToolDiscovery()
    
    print("=== 搜索GitHub工具 ===")
    task = "生成Excel表格"
    results = discovery.search_github_skills(task)
    
    for tool in results:
        print(f"\n工具: {tool['name']}")
        print(f"描述: {tool['description']}")
        print(f"URL: {tool['url']}")
        print(f"星标: {tool['stars']}")
        print(f"语言: {tool['language']}")
    
    print("\n\n=== 为任务推荐工具 ===")
    recommendations = discovery.recommend_tool_for_task(task)
    
    for rec in recommendations:
        tool = rec["tool_info"]
        eval_result = rec["evaluation"]
        
        print(f"\n推荐: {tool['name']}")
        print(f"适用: {eval_result['suitable']}")
        print(f"置信度: {eval_result['confidence']:.1%}")
        print(f"理由: {eval_result['reason']}")
        print(f"集成难度: {eval_result['integration_difficulty']}")
    
    print("\n\n=== 已集成的工具 ===")
    integrated = discovery.list_integrated_tools()
    print(f"总数: {len(integrated)}")
    for tool in integrated:
        print(f"- {tool['name']}: {tool['path']}")
