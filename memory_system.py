"""
记忆系统 (Memory System)
三层记忆：情景记忆、程序记忆、语义记忆
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import os
from datetime import datetime


@dataclass
class EpisodicMemory:
    """情景记忆：具体任务执行轨迹"""
    task_id: str
    timestamp: str
    input: str
    goals: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    result: Dict[str, Any]
    success: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProceduralMemory:
    """程序记忆："如何做"的技能流程"""
    skill_name: str
    description: str
    steps: List[str]
    success_rate: float
    usage_count: int
    last_used: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SemanticMemory:
    """语义记忆：领域知识、约束规则"""
    concept: str
    description: str
    category: str  # "knowledge" | "constraint" | "pattern"
    confidence: float
    source: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FailurePattern:
    """失败模式"""
    pattern_id: str
    error_type: str
    context: Dict[str, Any]
    frequency: int
    last_occurred: str
    mitigation: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MemorySystem:
    """
    三层记忆系统
    
    功能：
    1. 存储和检索情景记忆
    2. 提取和应用程序记忆
    3. 积累和查询语义记忆
    4. 记录和学习失败模式
    """
    
    def __init__(self, storage_dir: str = None):
        if storage_dir is None:
            storage_dir = os.path.join(os.path.dirname(__file__), ".memory")
        
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
        self.episodic_file = os.path.join(storage_dir, "episodic.jsonl")
        self.procedural_file = os.path.join(storage_dir, "procedural.json")
        self.semantic_file = os.path.join(storage_dir, "semantic.json")
        self.failure_file = os.path.join(storage_dir, "failures.json")
        
        # 内存缓存
        self.procedural_cache = self._load_procedural()
        self.semantic_cache = self._load_semantic()
        self.failure_cache = self._load_failures()
    
    # ========== 情景记忆 ==========
    
    def store_episode(self, episode: EpisodicMemory):
        """存储情景记忆"""
        with open(self.episodic_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(episode.to_dict(), ensure_ascii=False) + "\n")
    
    def retrieve_similar_episodes(self, query: str, limit: int = 5) -> List[EpisodicMemory]:
        """检索相似的情景记忆"""
        # 简化版本：实际应该使用向量相似度
        episodes = []
        
        if not os.path.exists(self.episodic_file):
            return episodes
        
        with open(self.episodic_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line)
                # 简单的关键词匹配
                if query.lower() in data.get("input", "").lower():
                    episodes.append(EpisodicMemory(**data))
                
                if len(episodes) >= limit:
                    break
        
        return episodes
    
    # ========== 程序记忆 ==========
    
    def _load_procedural(self) -> Dict[str, ProceduralMemory]:
        """加载程序记忆"""
        if not os.path.exists(self.procedural_file):
            return {}
        
        with open(self.procedural_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return {k: ProceduralMemory(**v) for k, v in data.items()}
    
    def _save_procedural(self):
        """保存程序记忆"""
        data = {k: v.to_dict() for k, v in self.procedural_cache.items()}
        with open(self.procedural_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def store_procedure(self, procedure: ProceduralMemory):
        """存储程序记忆"""
        self.procedural_cache[procedure.skill_name] = procedure
        self._save_procedural()
    
    def get_procedure(self, skill_name: str) -> Optional[ProceduralMemory]:
        """获取程序记忆"""
        return self.procedural_cache.get(skill_name)
    
    def update_procedure_stats(self, skill_name: str, success: bool):
        """更新程序记忆统计"""
        if skill_name not in self.procedural_cache:
            return
        
        proc = self.procedural_cache[skill_name]
        proc.usage_count += 1
        
        # 更新成功率（移动平均）
        alpha = 0.1  # 学习率
        if success:
            proc.success_rate = proc.success_rate * (1 - alpha) + alpha
        else:
            proc.success_rate = proc.success_rate * (1 - alpha)
        
        proc.last_used = datetime.now().isoformat()
        self._save_procedural()
    
    # ========== 语义记忆 ==========
    
    def _load_semantic(self) -> Dict[str, SemanticMemory]:
        """加载语义记忆"""
        if not os.path.exists(self.semantic_file):
            return {}
        
        with open(self.semantic_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return {k: SemanticMemory(**v) for k, v in data.items()}
    
    def _save_semantic(self):
        """保存语义记忆"""
        data = {k: v.to_dict() for k, v in self.semantic_cache.items()}
        with open(self.semantic_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def store_semantic(self, semantic: SemanticMemory):
        """存储语义记忆"""
        self.semantic_cache[semantic.concept] = semantic
        self._save_semantic()
    
    def query_semantic(self, concept: str) -> Optional[SemanticMemory]:
        """查询语义记忆"""
        return self.semantic_cache.get(concept)
    
    def query_semantic_by_category(self, category: str) -> List[SemanticMemory]:
        """按类别查询语义记忆"""
        return [s for s in self.semantic_cache.values() if s.category == category]
    
    # ========== 失败模式 ==========
    
    def _load_failures(self) -> Dict[str, FailurePattern]:
        """加载失败模式"""
        if not os.path.exists(self.failure_file):
            return {}
        
        with open(self.failure_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return {k: FailurePattern(**v) for k, v in data.items()}
    
    def _save_failures(self):
        """保存失败模式"""
        data = {k: v.to_dict() for k, v in self.failure_cache.items()}
        with open(self.failure_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def store_failure_pattern(self, pattern: FailurePattern):
        """存储失败模式"""
        if pattern.pattern_id in self.failure_cache:
            # 更新频率
            existing = self.failure_cache[pattern.pattern_id]
            existing.frequency += 1
            existing.last_occurred = pattern.last_occurred
        else:
            self.failure_cache[pattern.pattern_id] = pattern
        
        self._save_failures()
    
    def get_failure_pattern(self, pattern_id: str) -> Optional[FailurePattern]:
        """获取失败模式"""
        return self.failure_cache.get(pattern_id)
    
    def get_common_failures(self, limit: int = 10) -> List[FailurePattern]:
        """获取常见失败模式"""
        patterns = sorted(
            self.failure_cache.values(),
            key=lambda p: p.frequency,
            reverse=True
        )
        return patterns[:limit]
    
    # ========== 辅助方法 ==========
    
    def commit_success(self, task_id: str, input_data: str, goals: List[Dict], result: Dict):
        """提交成功案例"""
        episode = EpisodicMemory(
            task_id=task_id,
            timestamp=datetime.now().isoformat(),
            input=input_data,
            goals=goals,
            actions=[],  # 简化
            result=result,
            success=True
        )
        self.store_episode(episode)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆统计"""
        episodic_count = 0
        if os.path.exists(self.episodic_file):
            with open(self.episodic_file, "r") as f:
                episodic_count = sum(1 for line in f if line.strip())
        
        return {
            "episodic_memories": episodic_count,
            "procedural_skills": len(self.procedural_cache),
            "semantic_concepts": len(self.semantic_cache),
            "failure_patterns": len(self.failure_cache)
        }


# 全局单例
_memory_system = None

def get_memory_system() -> MemorySystem:
    """获取全局记忆系统实例"""
    global _memory_system
    if _memory_system is None:
        _memory_system = MemorySystem()
    return _memory_system
