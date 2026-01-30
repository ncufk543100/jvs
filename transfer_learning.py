"""
跨任务迁移学习 (Transfer Learning)
JARVIS Phase 4.2 - 将一个任务的经验应用到新任务

核心功能：
1. 提取任务模式和特征
2. 匹配相似任务
3. 迁移成功策略
4. 适应性调整
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re

class TransferLearner:
    """跨任务迁移学习器"""
    
    def __init__(self, data_dir: str = "/home/ubuntu/jarvis/data"):
        self.data_dir = data_dir
        self.task_patterns_file = os.path.join(data_dir, "task_patterns.json")
        
        os.makedirs(data_dir, exist_ok=True)
        
        # 加载任务模式库
        self.task_patterns = self._load_task_patterns()
    
    def extract_task_pattern(
        self,
        task_id: str,
        goal: str,
        strategy: str,
        tools_used: List[str],
        success: bool,
        duration: float,
        key_steps: List[str] = None
    ) -> Dict:
        """
        提取任务模式
        
        Args:
            task_id: 任务ID
            goal: 任务目标
            strategy: 使用的策略
            tools_used: 使用的工具列表
            success: 是否成功
            duration: 执行时长
            key_steps: 关键步骤（可选）
        
        Returns:
            Dict: 任务模式
        """
        pattern = {
            "task_id": task_id,
            "goal": goal,
            "task_type": self._classify_task_type(goal),
            "keywords": self._extract_keywords(goal),
            "strategy": strategy,
            "tools_used": tools_used,
            "success": success,
            "duration": duration,
            "key_steps": key_steps or [],
            "timestamp": datetime.now().isoformat()
        }
        
        # 保存到模式库
        self.task_patterns.append(pattern)
        self._save_task_patterns()
        
        return pattern
    
    def find_similar_tasks(
        self,
        goal: str,
        top_k: int = 3,
        min_similarity: float = 0.3
    ) -> List[Tuple[Dict, float]]:
        """
        查找相似任务
        
        Args:
            goal: 新任务目标
            top_k: 返回前K个最相似的
            min_similarity: 最小相似度阈值
        
        Returns:
            List[Tuple[Dict, float]]: [(任务模式, 相似度分数)]
        """
        if not self.task_patterns:
            return []
        
        new_task_type = self._classify_task_type(goal)
        new_keywords = self._extract_keywords(goal)
        
        similarities = []
        
        for pattern in self.task_patterns:
            if not pattern["success"]:
                continue  # 只参考成功的任务
            
            score = self._calculate_similarity(
                new_task_type,
                new_keywords,
                pattern["task_type"],
                pattern["keywords"]
            )
            
            if score >= min_similarity:
                similarities.append((pattern, score))
        
        # 按相似度排序
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def recommend_strategy(self, goal: str) -> Optional[Dict]:
        """
        为新任务推荐策略
        
        Args:
            goal: 新任务目标
        
        Returns:
            Dict: {
                "strategy": 推荐的策略,
                "tools": 推荐的工具列表,
                "confidence": 置信度,
                "reason": 推荐理由
            }
        """
        similar_tasks = self.find_similar_tasks(goal)
        
        if not similar_tasks:
            return None
        
        # 使用最相似任务的策略
        best_match, similarity = similar_tasks[0]
        
        return {
            "strategy": best_match["strategy"],
            "tools": best_match["tools_used"],
            "confidence": similarity,
            "reason": f"基于相似任务'{best_match['goal']}'的成功经验（相似度: {similarity:.1%}）",
            "reference_task_id": best_match["task_id"]
        }
    
    def get_transfer_learning_report(self) -> str:
        """
        生成迁移学习报告
        
        Returns:
            str: Markdown格式的报告
        """
        total_patterns = len(self.task_patterns)
        successful_patterns = sum(1 for p in self.task_patterns if p["success"])
        
        # 统计任务类型分布
        task_type_counts = {}
        for pattern in self.task_patterns:
            task_type = pattern["task_type"]
            task_type_counts[task_type] = task_type_counts.get(task_type, 0) + 1
        
        report = f"""## 迁移学习报告

### 任务模式库统计
- 总模式数：{total_patterns}
- 成功模式数：{successful_patterns}
- 成功率：{successful_patterns/total_patterns*100 if total_patterns > 0 else 0:.1f}%

### 任务类型分布
"""
        
        for task_type, count in sorted(task_type_counts.items(), key=lambda x: x[1], reverse=True):
            report += f"- **{task_type}**: {count}次\n"
        
        report += "\n### 最常用工具\n"
        
        # 统计工具使用频率
        tool_counts = {}
        for pattern in self.task_patterns:
            if pattern["success"]:
                for tool in pattern["tools_used"]:
                    tool_counts[tool] = tool_counts.get(tool, 0) + 1
        
        for tool, count in sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            report += f"- **{tool}**: {count}次\n"
        
        return report
    
    def _classify_task_type(self, goal: str) -> str:
        """
        分类任务类型
        
        使用关键词匹配进行简单分类
        """
        goal_lower = goal.lower()
        
        if any(kw in goal_lower for kw in ["创建", "生成", "编写", "写", "开发"]):
            return "creation"
        elif any(kw in goal_lower for kw in ["分析", "检查", "查看", "读取", "理解"]):
            return "analysis"
        elif any(kw in goal_lower for kw in ["修改", "更新", "优化", "改进", "重构"]):
            return "modification"
        elif any(kw in goal_lower for kw in ["测试", "验证", "检验", "调试"]):
            return "testing"
        elif any(kw in goal_lower for kw in ["部署", "安装", "配置", "设置"]):
            return "deployment"
        elif any(kw in goal_lower for kw in ["搜索", "查找", "定位"]):
            return "search"
        else:
            return "general"
    
    def _extract_keywords(self, goal: str) -> List[str]:
        """
        提取关键词
        
        简单实现：提取中文词和英文单词
        """
        # 移除标点符号
        goal = re.sub(r'[^\w\s]', ' ', goal)
        
        # 分词（简单按空格分）
        words = goal.split()
        
        # 过滤停用词和短词
        stopwords = {"的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这"}
        keywords = [w for w in words if len(w) > 1 and w not in stopwords]
        
        return keywords[:10]  # 最多保留10个关键词
    
    def _calculate_similarity(
        self,
        type1: str,
        keywords1: List[str],
        type2: str,
        keywords2: List[str]
    ) -> float:
        """
        计算任务相似度
        
        相似度 = 0.3 * 类型匹配 + 0.7 * 关键词重叠度
        """
        # 类型匹配
        type_score = 1.0 if type1 == type2 else 0.0
        
        # 关键词重叠度（Jaccard相似度）
        if not keywords1 or not keywords2:
            keyword_score = 0.0
        else:
            set1 = set(keywords1)
            set2 = set(keywords2)
            intersection = len(set1 & set2)
            union = len(set1 | set2)
            keyword_score = intersection / union if union > 0 else 0.0
        
        # 综合得分
        similarity = 0.3 * type_score + 0.7 * keyword_score
        
        return similarity
    
    def _load_task_patterns(self) -> List[Dict]:
        """加载任务模式"""
        if os.path.exists(self.task_patterns_file):
            try:
                with open(self.task_patterns_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_task_patterns(self) -> None:
        """保存任务模式"""
        with open(self.task_patterns_file, 'w', encoding='utf-8') as f:
            json.dump(self.task_patterns, f, ensure_ascii=False, indent=2)


# 全局实例
_transfer_learner = None

def get_transfer_learner() -> TransferLearner:
    """获取全局迁移学习器实例"""
    global _transfer_learner
    if _transfer_learner is None:
        _transfer_learner = TransferLearner()
    return _transfer_learner


if __name__ == "__main__":
    # 测试代码
    learner = TransferLearner()
    
    # 模拟几个任务模式
    learner.extract_task_pattern(
        task_id="task1",
        goal="创建一个Python脚本计算斐波那契数列",
        strategy="step_by_step",
        tools_used=["write_file", "run_shell"],
        success=True,
        duration=10.5,
        key_steps=["分析需求", "编写代码", "测试验证"]
    )
    
    learner.extract_task_pattern(
        task_id="task2",
        goal="编写Python函数判断质数",
        strategy="step_by_step",
        tools_used=["write_file", "run_shell"],
        success=True,
        duration=8.2,
        key_steps=["需求分析", "方案设计", "代码实现"]
    )
    
    learner.extract_task_pattern(
        task_id="task3",
        goal="分析日志文件找出错误",
        strategy="direct_execution",
        tools_used=["read_file", "run_shell"],
        success=True,
        duration=5.1
    )
    
    # 测试相似任务查找
    print("=== 查找相似任务 ===")
    new_goal = "创建Python脚本计算阶乘"
    similar = learner.find_similar_tasks(new_goal)
    for pattern, score in similar:
        print(f"相似度 {score:.1%}: {pattern['goal']}")
    
    # 测试策略推荐
    print("\n=== 策略推荐 ===")
    recommendation = learner.recommend_strategy(new_goal)
    if recommendation:
        print(f"推荐策略: {recommendation['strategy']}")
        print(f"推荐工具: {recommendation['tools']}")
        print(f"置信度: {recommendation['confidence']:.1%}")
        print(f"理由: {recommendation['reason']}")
    
    # 生成报告
    print("\n" + learner.get_transfer_learning_report())
