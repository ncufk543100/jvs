"""
用户反馈学习循环 (Feedback Learning Loop)
JARVIS Phase 4.1 - 从用户反馈中自动学习和改进

核心功能：
1. 收集任务执行数据和用户反馈
2. 分析成功/失败模式
3. 调整策略权重
4. 持久化学习结果
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict

class FeedbackLearner:
    """用户反馈学习器"""
    
    def __init__(self, data_dir: str = "/home/ubuntu/jarvis/data"):
        self.data_dir = data_dir
        self.feedback_file = os.path.join(data_dir, "feedback_history.json")
        self.strategy_weights_file = os.path.join(data_dir, "strategy_weights.json")
        
        # 确保数据目录存在
        os.makedirs(data_dir, exist_ok=True)
        
        # 加载历史数据
        self.feedback_history = self._load_feedback_history()
        self.strategy_weights = self._load_strategy_weights()
    
    def record_task_execution(
        self,
        task_id: str,
        goal: str,
        strategy: str,
        success: bool,
        duration: float,
        iterations: int,
        error_msg: Optional[str] = None,
        user_satisfaction: Optional[int] = None  # 1-5分
    ) -> None:
        """
        记录任务执行结果
        
        Args:
            task_id: 任务ID
            goal: 任务目标
            strategy: 使用的策略
            success: 是否成功
            duration: 执行时长（秒）
            iterations: 迭代次数
            error_msg: 错误信息（如果失败）
            user_satisfaction: 用户满意度（1-5分）
        """
        record = {
            "task_id": task_id,
            "goal": goal,
            "strategy": strategy,
            "success": success,
            "duration": duration,
            "iterations": iterations,
            "error_msg": error_msg,
            "user_satisfaction": user_satisfaction,
            "timestamp": datetime.now().isoformat()
        }
        
        self.feedback_history.append(record)
        self._save_feedback_history()
        
        # 自动学习：更新策略权重
        self._update_strategy_weights(strategy, success, user_satisfaction)
    
    def _update_strategy_weights(
        self,
        strategy: str,
        success: bool,
        user_satisfaction: Optional[int]
    ) -> None:
        """
        根据执行结果更新策略权重
        
        使用简单的增强学习：
        - 成功 → 权重+0.1
        - 失败 → 权重-0.05
        - 用户满意度高（4-5分）→ 额外+0.1
        - 用户满意度低（1-2分）→ 额外-0.1
        """
        if strategy not in self.strategy_weights:
            self.strategy_weights[strategy] = 1.0  # 初始权重
        
        # 基础调整
        if success:
            self.strategy_weights[strategy] += 0.1
        else:
            self.strategy_weights[strategy] -= 0.05
        
        # 用户满意度调整
        if user_satisfaction is not None:
            if user_satisfaction >= 4:
                self.strategy_weights[strategy] += 0.1
            elif user_satisfaction <= 2:
                self.strategy_weights[strategy] -= 0.1
        
        # 权重下限：不低于0.1
        self.strategy_weights[strategy] = max(0.1, self.strategy_weights[strategy])
        
        self._save_strategy_weights()
    
    def get_best_strategy(self, task_type: str = None) -> str:
        """
        获取当前最优策略
        
        Args:
            task_type: 任务类型（可选，用于细分）
        
        Returns:
            str: 推荐的策略名称
        """
        if not self.strategy_weights:
            return "default"
        
        # 返回权重最高的策略
        best_strategy = max(self.strategy_weights.items(), key=lambda x: x[1])
        return best_strategy[0]
    
    def analyze_failure_patterns(self) -> Dict[str, List[str]]:
        """
        分析失败模式
        
        Returns:
            Dict: {错误类型: [相关任务目标]}
        """
        failure_patterns = defaultdict(list)
        
        for record in self.feedback_history:
            if not record["success"] and record.get("error_msg"):
                error_type = self._classify_error(record["error_msg"])
                failure_patterns[error_type].append(record["goal"])
        
        return dict(failure_patterns)
    
    def _classify_error(self, error_msg: str) -> str:
        """简单的错误分类"""
        error_msg_lower = error_msg.lower()
        
        if "timeout" in error_msg_lower:
            return "timeout"
        elif "permission" in error_msg_lower or "access denied" in error_msg_lower:
            return "permission"
        elif "file not found" in error_msg_lower or "no such file" in error_msg_lower:
            return "file_not_found"
        elif "network" in error_msg_lower or "connection" in error_msg_lower:
            return "network"
        elif "syntax" in error_msg_lower or "parse" in error_msg_lower:
            return "syntax"
        else:
            return "unknown"
    
    def get_success_rate(self, strategy: str = None, last_n: int = None) -> float:
        """
        计算成功率
        
        Args:
            strategy: 特定策略（可选）
            last_n: 只统计最近N次（可选）
        
        Returns:
            float: 成功率（0.0-1.0）
        """
        records = self.feedback_history
        
        if last_n:
            records = records[-last_n:]
        
        if strategy:
            records = [r for r in records if r["strategy"] == strategy]
        
        if not records:
            return 0.0
        
        success_count = sum(1 for r in records if r["success"])
        return success_count / len(records)
    
    def get_learning_report(self) -> str:
        """
        生成学习报告
        
        Returns:
            str: Markdown格式的报告
        """
        total_tasks = len(self.feedback_history)
        if total_tasks == 0:
            return "## 学习报告\n\n暂无执行记录。"
        
        success_rate = self.get_success_rate()
        failure_patterns = self.analyze_failure_patterns()
        
        report = f"""## 学习报告

### 总体统计
- 总任务数：{total_tasks}
- 总成功率：{success_rate:.1%}
- 策略数量：{len(self.strategy_weights)}

### 策略权重排名
"""
        
        sorted_strategies = sorted(
            self.strategy_weights.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for i, (strategy, weight) in enumerate(sorted_strategies[:5], 1):
            strategy_success_rate = self.get_success_rate(strategy=strategy)
            report += f"{i}. **{strategy}**: 权重 {weight:.2f}, 成功率 {strategy_success_rate:.1%}\n"
        
        report += "\n### 失败模式分析\n"
        
        if failure_patterns:
            for error_type, goals in failure_patterns.items():
                report += f"- **{error_type}**: {len(goals)}次\n"
        else:
            report += "暂无失败记录。\n"
        
        return report
    
    def _load_feedback_history(self) -> List[Dict]:
        """加载反馈历史"""
        if os.path.exists(self.feedback_file):
            try:
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_feedback_history(self) -> None:
        """保存反馈历史"""
        with open(self.feedback_file, 'w', encoding='utf-8') as f:
            json.dump(self.feedback_history, f, ensure_ascii=False, indent=2)
    
    def _load_strategy_weights(self) -> Dict[str, float]:
        """加载策略权重"""
        if os.path.exists(self.strategy_weights_file):
            try:
                with open(self.strategy_weights_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_strategy_weights(self) -> None:
        """保存策略权重"""
        with open(self.strategy_weights_file, 'w', encoding='utf-8') as f:
            json.dump(self.strategy_weights, f, ensure_ascii=False, indent=2)


# 全局实例
_learner = None

def get_learner() -> FeedbackLearner:
    """获取全局学习器实例"""
    global _learner
    if _learner is None:
        _learner = FeedbackLearner()
    return _learner


if __name__ == "__main__":
    # 测试代码
    learner = FeedbackLearner()
    
    # 模拟几次任务执行
    learner.record_task_execution(
        task_id="task1",
        goal="创建Python脚本",
        strategy="direct_execution",
        success=True,
        duration=5.2,
        iterations=1,
        user_satisfaction=5
    )
    
    learner.record_task_execution(
        task_id="task2",
        goal="分析数据",
        strategy="step_by_step",
        success=False,
        duration=10.5,
        iterations=3,
        error_msg="File not found: data.csv"
    )
    
    learner.record_task_execution(
        task_id="task3",
        goal="生成报告",
        strategy="direct_execution",
        success=True,
        duration=8.1,
        iterations=2,
        user_satisfaction=4
    )
    
    # 生成报告
    print(learner.get_learning_report())
    print(f"\n推荐策略: {learner.get_best_strategy()}")
