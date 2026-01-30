"""
JARVIS 结构化任务规划系统
模仿 Manus 的 phase 机制，实现多阶段任务规划和执行
"""

import json
from typing import List, Dict, Optional
from event_bus import emit

class Phase:
    """任务阶段"""
    def __init__(self, id: int, title: str, description: str, capabilities: Dict[str, bool] = None):
        self.id = id
        self.title = title
        self.description = description
        self.capabilities = capabilities or {}
        self.status = "pending"  # pending, in_progress, completed, failed
        self.result = None
        self.error = None
    
    def mark_completed(self, result: str = None):
        """标记阶段完成"""
        self.status = "completed"
        self.result = result
        emit("phase_completed", f"✅ 阶段 {self.id} 完成: {self.title}")
    
    def mark_failed(self, error: str):
        """标记阶段失败"""
        self.status = "failed"
        self.error = error
        emit("phase_failed", f"❌ 阶段 {self.id} 失败: {error}")
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "capabilities": self.capabilities,
            "status": self.status,
            "result": self.result,
            "error": self.error
        }

class TaskPlan:
    """任务计划"""
    def __init__(self, goal: str):
        self.goal = goal
        self.phases: List[Phase] = []
        self.current_phase_id = 0
        self.status = "planning"  # planning, executing, completed, failed
    
    def add_phase(self, title: str, description: str, capabilities: Dict[str, bool] = None) -> Phase:
        """添加阶段"""
        phase_id = len(self.phases) + 1
        phase = Phase(phase_id, title, description, capabilities)
        self.phases.append(phase)
        return phase
    
    def get_current_phase(self) -> Optional[Phase]:
        """获取当前阶段"""
        if 0 < self.current_phase_id <= len(self.phases):
            return self.phases[self.current_phase_id - 1]
        return None
    
    def advance(self) -> bool:
        """推进到下一阶段"""
        current = self.get_current_phase()
        if current:
            current.status = "completed"
        
        if self.current_phase_id < len(self.phases):
            self.current_phase_id += 1
            next_phase = self.get_current_phase()
            if next_phase:
                next_phase.status = "in_progress"
                emit("phase_advance", f"进入阶段 {next_phase.id}: {next_phase.title}")
                return True
        else:
            self.status = "completed"
            emit("plan_complete", "所有阶段已完成")
            return False
        return False
    
    def fail_current_phase(self, error: str):
        """标记当前阶段失败"""
        current = self.get_current_phase()
        if current:
            current.status = "failed"
            current.error = error
            self.status = "failed"
            emit("phase_failed", f"阶段 {current.id} 失败: {error}")
    
    def to_dict(self):
        return {
            "goal": self.goal,
            "phases": [p.to_dict() for p in self.phases],
            "current_phase_id": self.current_phase_id,
            "status": self.status
        }
    
    def save(self, path: str = "TASK_PLAN.json"):
        """保存计划到文件"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load(cls, path: str = "TASK_PLAN.json") -> Optional['TaskPlan']:
        """从文件加载计划"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            plan = cls(data["goal"])
            plan.current_phase_id = data["current_phase_id"]
            plan.status = data["status"]
            
            for p_data in data["phases"]:
                phase = Phase(
                    p_data["id"],
                    p_data["title"],
                    p_data["description"],
                    p_data.get("capabilities", {})
                )
                phase.status = p_data.get("status", "pending")
                phase.result = p_data.get("result")
                phase.error = p_data.get("error")
                plan.phases.append(phase)
            
            return plan
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return None

class Planner:
    """任务规划器"""
    
    @staticmethod
    def create_plan(goal: str, complexity: str = "medium") -> TaskPlan:
        """
        根据目标创建任务计划
        
        Args:
            goal: 任务目标
            complexity: 复杂度 (simple, medium, complex)
        
        Returns:
            TaskPlan: 任务计划
        """
        plan = TaskPlan(goal)
        
        # 根据复杂度决定阶段数量
        if complexity == "simple":
            plan.add_phase(
                "理解任务",
                "分析用户需求，明确任务目标"
            )
            plan.add_phase(
                "执行任务",
                "执行具体操作，完成任务目标"
            )
            plan.add_phase(
                "验证结果",
                "验证任务执行结果，确保符合预期"
            )
        
        elif complexity == "medium":
            plan.add_phase(
                "需求分析",
                "深入理解用户需求，识别关键要素"
            )
            plan.add_phase(
                "方案设计",
                "设计解决方案，规划执行步骤"
            )
            plan.add_phase(
                "资源准备",
                "准备必要的工具、数据和环境"
            )
            plan.add_phase(
                "执行实施",
                "按照方案执行具体操作"
            )
            plan.add_phase(
                "测试验证",
                "测试执行结果，验证是否达标"
            )
            plan.add_phase(
                "交付总结",
                "整理结果，交付给用户"
            )
        
        elif complexity == "complex":
            plan.add_phase(
                "需求调研",
                "全面调研用户需求，收集相关信息"
            )
            plan.add_phase(
                "可行性分析",
                "评估技术可行性和资源可用性"
            )
            plan.add_phase(
                "架构设计",
                "设计整体架构和模块划分"
            )
            plan.add_phase(
                "环境搭建",
                "搭建开发、测试和生产环境"
            )
            plan.add_phase(
                "核心开发",
                "开发核心功能模块"
            )
            plan.add_phase(
                "功能扩展",
                "开发辅助功能和优化"
            )
            plan.add_phase(
                "集成测试",
                "进行全面的集成测试"
            )
            plan.add_phase(
                "性能优化",
                "优化性能和用户体验"
            )
            plan.add_phase(
                "部署上线",
                "部署到生产环境"
            )
            plan.add_phase(
                "文档交付",
                "编写文档，交付给用户"
            )
        
        # 设置第一个阶段为进行中
        if plan.phases:
            plan.current_phase_id = 1
            plan.phases[0].status = "in_progress"
            plan.status = "executing"
        
        emit("plan_created", f"已创建 {len(plan.phases)} 阶段的任务计划")
        return plan
    
    @staticmethod
    def analyze_complexity(goal: str) -> str:
        """
        分析任务复杂度
        
        Args:
            goal: 任务目标
        
        Returns:
            str: 复杂度等级 (simple, medium, complex)
        """
        goal_lower = goal.lower()
        
        # 简单任务关键词
        simple_keywords = ["计算", "查询", "搜索", "打开", "关闭", "查看", "显示"]
        
        # 复杂任务关键词
        complex_keywords = ["开发", "构建", "设计", "实现", "创建系统", "搭建平台", "完整的"]
        
        # 检查复杂任务
        if any(kw in goal_lower for kw in complex_keywords):
            return "complex"
        
        # 检查简单任务
        if any(kw in goal_lower for kw in simple_keywords) and len(goal) < 20:
            return "simple"
        
        # 默认中等复杂度
        return "medium"

# 使用示例
if __name__ == "__main__":
    # 创建计划
    planner = Planner()
    goal = "开发一个完整的任务管理系统"
    complexity = planner.analyze_complexity(goal)
    plan = planner.create_plan(goal, complexity)
    
    print(f"目标: {plan.goal}")
    print(f"复杂度: {complexity}")
    print(f"阶段数: {len(plan.phases)}")
    print("\n阶段列表:")
    for phase in plan.phases:
        print(f"  {phase.id}. {phase.title} - {phase.description}")
    
    # 保存计划
    plan.save()
    print("\n计划已保存到 TASK_PLAN.json")
