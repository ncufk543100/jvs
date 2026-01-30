"""
持续进化循环 (Evolution Loop)
JARVIS Phase 4.4 - 自动性能监控、优化和部署

核心功能：
1. 性能监控和数据收集
2. 瓶颈分析和优化建议
3. 自动代码优化
4. 版本管理和回滚
"""

import json
import os
import time
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

class PerformanceMetrics:
    """性能指标"""
    def __init__(self):
        self.metrics = {
            "task_count": 0,
            "success_count": 0,
            "failure_count": 0,
            "total_duration": 0.0,
            "avg_duration": 0.0,
            "avg_iterations": 0.0,
            "tool_usage": defaultdict(int),
            "error_types": defaultdict(int)
        }
    
    def record(
        self,
        success: bool,
        duration: float,
        iterations: int,
        tools_used: List[str],
        error_type: str = None
    ) -> None:
        """记录一次任务执行"""
        self.metrics["task_count"] += 1
        
        if success:
            self.metrics["success_count"] += 1
        else:
            self.metrics["failure_count"] += 1
            if error_type:
                self.metrics["error_types"][error_type] += 1
        
        self.metrics["total_duration"] += duration
        self.metrics["avg_duration"] = (
            self.metrics["total_duration"] / self.metrics["task_count"]
        )
        
        # 更新平均迭代次数
        total_iterations = (
            self.metrics["avg_iterations"] * (self.metrics["task_count"] - 1) + iterations
        )
        self.metrics["avg_iterations"] = total_iterations / self.metrics["task_count"]
        
        # 记录工具使用
        for tool in tools_used:
            self.metrics["tool_usage"][tool] += 1
    
    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.metrics["task_count"] == 0:
            return 0.0
        return self.metrics["success_count"] / self.metrics["task_count"]
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            **self.metrics,
            "tool_usage": dict(self.metrics["tool_usage"]),
            "error_types": dict(self.metrics["error_types"]),
            "success_rate": self.get_success_rate()
        }


class EvolutionLoop:
    """持续进化循环"""
    
    def __init__(self, data_dir: str = "/home/ubuntu/jarvis/data"):
        self.data_dir = data_dir
        self.metrics_file = os.path.join(data_dir, "performance_metrics.json")
        self.evolution_log_file = os.path.join(data_dir, "evolution_log.json")
        self.backup_dir = os.path.join(data_dir, "../.backups")
        
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # 当前性能指标
        self.current_metrics = PerformanceMetrics()
        
        # 进化日志
        self.evolution_log = self._load_evolution_log()
        
        # 加载历史指标
        self._load_metrics()
    
    def monitor_task(
        self,
        task_id: str,
        success: bool,
        duration: float,
        iterations: int,
        tools_used: List[str],
        error_type: str = None
    ) -> None:
        """
        监控任务执行
        
        Args:
            task_id: 任务ID
            success: 是否成功
            duration: 执行时长
            iterations: 迭代次数
            tools_used: 使用的工具
            error_type: 错误类型（如果失败）
        """
        self.current_metrics.record(success, duration, iterations, tools_used, error_type)
        self._save_metrics()
        
        # 检查是否需要触发优化
        if self.current_metrics.metrics["task_count"] % 10 == 0:
            self._check_and_optimize()
    
    def _check_and_optimize(self) -> None:
        """检查并优化"""
        bottlenecks = self.analyze_bottlenecks()
        
        if bottlenecks:
            print(f"\n🔍 检测到 {len(bottlenecks)} 个性能瓶颈")
            
            for bottleneck in bottlenecks:
                print(f"  - {bottleneck['type']}: {bottleneck['description']}")
                
                # 生成优化建议
                suggestions = self._generate_optimization_suggestions(bottleneck)
                
                if suggestions:
                    print(f"    优化建议: {suggestions[0]}")
                    
                    # 记录到进化日志
                    self._log_evolution_event(
                        event_type="bottleneck_detected",
                        description=bottleneck['description'],
                        suggestions=suggestions
                    )
    
    def analyze_bottlenecks(self) -> List[Dict]:
        """
        分析性能瓶颈
        
        Returns:
            List[Dict]: 瓶颈列表
        """
        bottlenecks = []
        metrics = self.current_metrics.metrics
        
        # 1. 成功率过低
        success_rate = self.current_metrics.get_success_rate()
        if success_rate < 0.7:
            bottlenecks.append({
                "type": "low_success_rate",
                "description": f"成功率过低 ({success_rate:.1%})",
                "severity": "high"
            })
        
        # 2. 平均执行时间过长
        if metrics["avg_duration"] > 30.0:
            bottlenecks.append({
                "type": "slow_execution",
                "description": f"平均执行时间过长 ({metrics['avg_duration']:.1f}秒)",
                "severity": "medium"
            })
        
        # 3. 平均迭代次数过多
        if metrics["avg_iterations"] > 5.0:
            bottlenecks.append({
                "type": "too_many_iterations",
                "description": f"平均迭代次数过多 ({metrics['avg_iterations']:.1f}次)",
                "severity": "medium"
            })
        
        # 4. 特定错误频繁出现
        for error_type, count in metrics["error_types"].items():
            if count > metrics["task_count"] * 0.2:  # 超过20%
                bottlenecks.append({
                    "type": "frequent_error",
                    "description": f"错误 '{error_type}' 频繁出现 ({count}次)",
                    "severity": "high",
                    "error_type": error_type
                })
        
        return bottlenecks
    
    def _generate_optimization_suggestions(self, bottleneck: Dict) -> List[str]:
        """
        生成优化建议
        
        Args:
            bottleneck: 瓶颈信息
        
        Returns:
            List[str]: 优化建议列表
        """
        suggestions = []
        
        if bottleneck["type"] == "low_success_rate":
            suggestions.append("增强错误处理和重试机制")
            suggestions.append("改进任务规划策略")
            suggestions.append("添加更多的前置检查")
        
        elif bottleneck["type"] == "slow_execution":
            suggestions.append("优化工具执行效率")
            suggestions.append("减少不必要的中间步骤")
            suggestions.append("并行执行独立任务")
        
        elif bottleneck["type"] == "too_many_iterations":
            suggestions.append("改进初始规划质量")
            suggestions.append("增强意图推断能力")
            suggestions.append("优化反馈学习机制")
        
        elif bottleneck["type"] == "frequent_error":
            error_type = bottleneck.get("error_type", "")
            if "file" in error_type.lower():
                suggestions.append("添加文件存在性检查")
                suggestions.append("改进文件路径处理")
            elif "permission" in error_type.lower():
                suggestions.append("检查文件权限")
                suggestions.append("使用sudo执行需要权限的操作")
            elif "timeout" in error_type.lower():
                suggestions.append("增加超时时间")
                suggestions.append("优化长时间运行的操作")
        
        return suggestions
    
    def create_backup(self, version: str = None) -> str:
        """
        创建代码备份
        
        Args:
            version: 版本号（可选，自动生成）
        
        Returns:
            str: 备份路径
        """
        if version is None:
            version = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        backup_path = os.path.join(self.backup_dir, f"backup_{version}")
        
        # 备份核心文件
        core_files = [
            "agent.py",
            "agent_with_planner.py",
            "executor.py",
            "llm.py",
            "planner.py",
            "feedback_learner.py",
            "transfer_learning.py",
            "knowledge_graph.py",
            "evolution_loop.py"
        ]
        
        os.makedirs(backup_path, exist_ok=True)
        
        for file in core_files:
            src = os.path.join("/home/ubuntu/jarvis", file)
            if os.path.exists(src):
                shutil.copy2(src, backup_path)
        
        print(f"✅ 备份已创建: {backup_path}")
        
        # 记录到进化日志
        self._log_evolution_event(
            event_type="backup_created",
            description=f"版本 {version} 备份已创建",
            version=version,
            backup_path=backup_path
        )
        
        return backup_path
    
    def rollback(self, version: str) -> bool:
        """
        回滚到指定版本
        
        Args:
            version: 版本号
        
        Returns:
            bool: 是否成功
        """
        backup_path = os.path.join(self.backup_dir, f"backup_{version}")
        
        if not os.path.exists(backup_path):
            print(f"❌ 备份不存在: {backup_path}")
            return False
        
        # 先创建当前版本的备份
        current_backup = self.create_backup(version=f"before_rollback_{int(time.time())}")
        
        # 恢复文件
        for file in os.listdir(backup_path):
            src = os.path.join(backup_path, file)
            dst = os.path.join("/home/ubuntu/jarvis", file)
            shutil.copy2(src, dst)
        
        print(f"✅ 已回滚到版本: {version}")
        
        # 记录到进化日志
        self._log_evolution_event(
            event_type="rollback",
            description=f"回滚到版本 {version}",
            version=version,
            previous_backup=current_backup
        )
        
        return True
    
    def get_evolution_report(self) -> str:
        """
        生成进化报告
        
        Returns:
            str: Markdown格式的报告
        """
        metrics = self.current_metrics.to_dict()
        bottlenecks = self.analyze_bottlenecks()
        
        report = f"""## 进化报告

### 性能指标
- 总任务数：{metrics['task_count']}
- 成功率：{metrics['success_rate']:.1%}
- 平均执行时间：{metrics['avg_duration']:.1f}秒
- 平均迭代次数：{metrics['avg_iterations']:.1f}次

### 工具使用统计
"""
        
        sorted_tools = sorted(
            metrics['tool_usage'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for tool, count in sorted_tools[:5]:
            report += f"- **{tool}**: {count}次\n"
        
        report += "\n### 性能瓶颈\n"
        
        if bottlenecks:
            for bottleneck in bottlenecks:
                report += f"- [{bottleneck['severity'].upper()}] {bottleneck['description']}\n"
        else:
            report += "暂无明显瓶颈。\n"
        
        report += f"\n### 进化事件\n"
        report += f"总事件数：{len(self.evolution_log)}\n"
        
        # 显示最近5个事件
        recent_events = self.evolution_log[-5:]
        for event in recent_events:
            report += f"- [{event['timestamp']}] {event['event_type']}: {event['description']}\n"
        
        return report
    
    def _log_evolution_event(self, event_type: str, description: str, **kwargs) -> None:
        """记录进化事件"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "description": description,
            **kwargs
        }
        
        self.evolution_log.append(event)
        self._save_evolution_log()
    
    def _load_metrics(self) -> None:
        """加载性能指标"""
        if os.path.exists(self.metrics_file):
            try:
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.current_metrics.metrics.update(data)
                    # 恢复defaultdict
                    self.current_metrics.metrics["tool_usage"] = defaultdict(
                        int,
                        data.get("tool_usage", {})
                    )
                    self.current_metrics.metrics["error_types"] = defaultdict(
                        int,
                        data.get("error_types", {})
                    )
            except:
                pass
    
    def _save_metrics(self) -> None:
        """保存性能指标"""
        with open(self.metrics_file, 'w', encoding='utf-8') as f:
            json.dump(self.current_metrics.to_dict(), f, ensure_ascii=False, indent=2)
    
    def _load_evolution_log(self) -> List[Dict]:
        """加载进化日志"""
        if os.path.exists(self.evolution_log_file):
            try:
                with open(self.evolution_log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_evolution_log(self) -> None:
        """保存进化日志"""
        with open(self.evolution_log_file, 'w', encoding='utf-8') as f:
            json.dump(self.evolution_log, f, ensure_ascii=False, indent=2)


# 全局实例
_evolution_loop = None

def get_evolution_loop() -> EvolutionLoop:
    """获取全局进化循环实例"""
    global _evolution_loop
    if _evolution_loop is None:
        _evolution_loop = EvolutionLoop()
    return _evolution_loop


if __name__ == "__main__":
    # 测试代码
    loop = EvolutionLoop()
    
    # 模拟任务执行
    print("=== 模拟任务执行 ===")
    for i in range(15):
        success = i % 3 != 0  # 模拟失败
        duration = 5.0 + i * 0.5
        iterations = 1 + i % 4
        tools = ["write_file", "run_shell"] if i % 2 == 0 else ["read_file"]
        error = "file_not_found" if not success else None
        
        loop.monitor_task(
            task_id=f"task_{i}",
            success=success,
            duration=duration,
            iterations=iterations,
            tools_used=tools,
            error_type=error
        )
    
    # 创建备份
    print("\n=== 创建备份 ===")
    loop.create_backup("test_v1.0")
    
    # 生成报告
    print("\n" + loop.get_evolution_report())
