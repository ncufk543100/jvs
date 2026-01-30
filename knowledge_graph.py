"""
知识图谱系统 (Knowledge Graph)
JARVIS Phase 4.3 - 结构化知识存储和关系推理

核心功能：
1. 实体和关系管理
2. 知识查询和推理
3. 知识演化和更新
4. 图谱可视化（文本格式）
"""

import json
import os
from typing import Dict, List, Set, Optional, Tuple
from datetime import datetime
from collections import defaultdict

class Entity:
    """实体节点"""
    def __init__(self, id: str, type: str, properties: Dict = None):
        self.id = id
        self.type = type  # 如：tool, concept, task, error, solution
        self.properties = properties or {}
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type,
            "properties": self.properties,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Entity':
        entity = cls(data["id"], data["type"], data.get("properties", {}))
        entity.created_at = data.get("created_at", entity.created_at)
        return entity


class Relation:
    """关系边"""
    def __init__(self, source_id: str, relation_type: str, target_id: str, properties: Dict = None):
        self.source_id = source_id
        self.relation_type = relation_type  # 如：uses, solves, causes, requires
        self.target_id = target_id
        self.properties = properties or {}
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            "source_id": self.source_id,
            "relation_type": self.relation_type,
            "target_id": self.target_id,
            "properties": self.properties,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Relation':
        relation = cls(
            data["source_id"],
            data["relation_type"],
            data["target_id"],
            data.get("properties", {})
        )
        relation.created_at = data.get("created_at", relation.created_at)
        return relation


class KnowledgeGraph:
    """知识图谱"""
    
    def __init__(self, data_dir: str = "/home/ubuntu/jarvis/data"):
        self.data_dir = data_dir
        self.graph_file = os.path.join(data_dir, "knowledge_graph.json")
        
        os.makedirs(data_dir, exist_ok=True)
        
        # 实体和关系存储
        self.entities: Dict[str, Entity] = {}
        self.relations: List[Relation] = []
        
        # 索引（加速查询）
        self._rebuild_indexes()
        
        # 加载图谱
        self._load_graph()
    
    def add_entity(self, id: str, type: str, properties: Dict = None) -> Entity:
        """添加实体"""
        if id in self.entities:
            # 更新现有实体
            self.entities[id].properties.update(properties or {})
        else:
            # 创建新实体
            entity = Entity(id, type, properties)
            self.entities[id] = entity
        
        self._rebuild_indexes()
        self._save_graph()
        return self.entities[id]
    
    def add_relation(
        self,
        source_id: str,
        relation_type: str,
        target_id: str,
        properties: Dict = None
    ) -> Relation:
        """添加关系"""
        # 检查实体是否存在
        if source_id not in self.entities or target_id not in self.entities:
            raise ValueError(f"实体不存在: {source_id} 或 {target_id}")
        
        # 检查关系是否已存在
        for rel in self.relations:
            if (rel.source_id == source_id and 
                rel.relation_type == relation_type and 
                rel.target_id == target_id):
                # 更新现有关系
                rel.properties.update(properties or {})
                self._save_graph()
                return rel
        
        # 创建新关系
        relation = Relation(source_id, relation_type, target_id, properties)
        self.relations.append(relation)
        
        self._rebuild_indexes()
        self._save_graph()
        return relation
    
    def get_entity(self, id: str) -> Optional[Entity]:
        """获取实体"""
        return self.entities.get(id)
    
    def find_entities(self, type: str = None, **property_filters) -> List[Entity]:
        """
        查找实体
        
        Args:
            type: 实体类型过滤
            **property_filters: 属性过滤条件
        
        Returns:
            List[Entity]: 匹配的实体列表
        """
        results = []
        
        for entity in self.entities.values():
            # 类型过滤
            if type and entity.type != type:
                continue
            
            # 属性过滤
            match = True
            for key, value in property_filters.items():
                if entity.properties.get(key) != value:
                    match = False
                    break
            
            if match:
                results.append(entity)
        
        return results
    
    def get_neighbors(
        self,
        entity_id: str,
        relation_type: str = None,
        direction: str = "both"  # "out", "in", "both"
    ) -> List[Tuple[Entity, Relation]]:
        """
        获取邻居节点
        
        Args:
            entity_id: 实体ID
            relation_type: 关系类型过滤（可选）
            direction: 方向（out=出边, in=入边, both=双向）
        
        Returns:
            List[Tuple[Entity, Relation]]: [(邻居实体, 关系)]
        """
        neighbors = []
        
        for relation in self.relations:
            # 出边
            if direction in ["out", "both"] and relation.source_id == entity_id:
                if relation_type is None or relation.relation_type == relation_type:
                    target = self.entities.get(relation.target_id)
                    if target:
                        neighbors.append((target, relation))
            
            # 入边
            if direction in ["in", "both"] and relation.target_id == entity_id:
                if relation_type is None or relation.relation_type == relation_type:
                    source = self.entities.get(relation.source_id)
                    if source:
                        neighbors.append((source, relation))
        
        return neighbors
    
    def find_path(
        self,
        start_id: str,
        end_id: str,
        max_depth: int = 3
    ) -> Optional[List[Tuple[Entity, Relation]]]:
        """
        查找两个实体之间的路径（BFS）
        
        Args:
            start_id: 起始实体ID
            end_id: 目标实体ID
            max_depth: 最大搜索深度
        
        Returns:
            Optional[List[Tuple[Entity, Relation]]]: 路径（如果存在）
        """
        if start_id not in self.entities or end_id not in self.entities:
            return None
        
        if start_id == end_id:
            return []
        
        # BFS搜索
        queue = [(start_id, [])]
        visited = {start_id}
        
        while queue:
            current_id, path = queue.pop(0)
            
            if len(path) >= max_depth:
                continue
            
            neighbors = self.get_neighbors(current_id, direction="out")
            
            for neighbor, relation in neighbors:
                if neighbor.id == end_id:
                    return path + [(neighbor, relation)]
                
                if neighbor.id not in visited:
                    visited.add(neighbor.id)
                    queue.append((neighbor.id, path + [(neighbor, relation)]))
        
        return None
    
    def infer_relations(self, entity_id: str) -> List[Tuple[str, str, str]]:
        """
        推理新关系
        
        简单推理规则：
        - 如果 A uses B, B solves C, 则推理 A solves C
        - 如果 A requires B, B requires C, 则推理 A requires C
        
        Args:
            entity_id: 实体ID
        
        Returns:
            List[Tuple[str, str, str]]: [(source_id, relation_type, target_id)]
        """
        inferred = []
        
        # 规则1: 传递性推理 (uses -> solves)
        neighbors_1 = self.get_neighbors(entity_id, relation_type="uses", direction="out")
        for neighbor_1, _ in neighbors_1:
            neighbors_2 = self.get_neighbors(neighbor_1.id, relation_type="solves", direction="out")
            for neighbor_2, _ in neighbors_2:
                # 检查是否已存在
                exists = any(
                    r.source_id == entity_id and 
                    r.relation_type == "solves" and 
                    r.target_id == neighbor_2.id
                    for r in self.relations
                )
                if not exists:
                    inferred.append((entity_id, "solves", neighbor_2.id))
        
        # 规则2: 传递性推理 (requires)
        neighbors_1 = self.get_neighbors(entity_id, relation_type="requires", direction="out")
        for neighbor_1, _ in neighbors_1:
            neighbors_2 = self.get_neighbors(neighbor_1.id, relation_type="requires", direction="out")
            for neighbor_2, _ in neighbors_2:
                exists = any(
                    r.source_id == entity_id and 
                    r.relation_type == "requires" and 
                    r.target_id == neighbor_2.id
                    for r in self.relations
                )
                if not exists:
                    inferred.append((entity_id, "requires", neighbor_2.id))
        
        return inferred
    
    def get_statistics(self) -> Dict:
        """获取图谱统计信息"""
        entity_type_counts = defaultdict(int)
        for entity in self.entities.values():
            entity_type_counts[entity.type] += 1
        
        relation_type_counts = defaultdict(int)
        for relation in self.relations:
            relation_type_counts[relation.relation_type] += 1
        
        return {
            "total_entities": len(self.entities),
            "total_relations": len(self.relations),
            "entity_types": dict(entity_type_counts),
            "relation_types": dict(relation_type_counts)
        }
    
    def visualize(self, center_id: str = None, depth: int = 1) -> str:
        """
        可视化图谱（文本格式）
        
        Args:
            center_id: 中心节点ID（可选）
            depth: 显示深度
        
        Returns:
            str: 文本格式的图谱
        """
        if center_id:
            # 显示以某个节点为中心的子图
            return self._visualize_subgraph(center_id, depth)
        else:
            # 显示整个图谱
            return self._visualize_full_graph()
    
    def _visualize_subgraph(self, center_id: str, depth: int) -> str:
        """可视化子图"""
        if center_id not in self.entities:
            return f"实体不存在: {center_id}"
        
        center = self.entities[center_id]
        lines = [f"## 知识图谱（中心: {center.id}）\n"]
        lines.append(f"**{center.id}** ({center.type})")
        
        visited = {center_id}
        queue = [(center_id, 0)]
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_depth >= depth:
                continue
            
            neighbors = self.get_neighbors(current_id, direction="out")
            
            for neighbor, relation in neighbors:
                indent = "  " * (current_depth + 1)
                lines.append(f"{indent}--[{relation.relation_type}]--> **{neighbor.id}** ({neighbor.type})")
                
                if neighbor.id not in visited:
                    visited.add(neighbor.id)
                    queue.append((neighbor.id, current_depth + 1))
        
        return "\n".join(lines)
    
    def _visualize_full_graph(self) -> str:
        """可视化完整图谱"""
        lines = ["## 完整知识图谱\n"]
        lines.append(f"实体数: {len(self.entities)}, 关系数: {len(self.relations)}\n")
        
        for relation in self.relations:
            source = self.entities.get(relation.source_id)
            target = self.entities.get(relation.target_id)
            if source and target:
                lines.append(
                    f"**{source.id}** ({source.type}) "
                    f"--[{relation.relation_type}]--> "
                    f"**{target.id}** ({target.type})"
                )
        
        return "\n".join(lines)
    
    def _rebuild_indexes(self) -> None:
        """重建索引"""
        # 可以在这里添加更复杂的索引结构
        pass
    
    def _load_graph(self) -> None:
        """加载图谱"""
        if os.path.exists(self.graph_file):
            try:
                with open(self.graph_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # 加载实体
                    for entity_data in data.get("entities", []):
                        entity = Entity.from_dict(entity_data)
                        self.entities[entity.id] = entity
                    
                    # 加载关系
                    for relation_data in data.get("relations", []):
                        relation = Relation.from_dict(relation_data)
                        self.relations.append(relation)
                    
                    self._rebuild_indexes()
            except:
                pass
    
    def _save_graph(self) -> None:
        """保存图谱"""
        data = {
            "entities": [e.to_dict() for e in self.entities.values()],
            "relations": [r.to_dict() for r in self.relations]
        }
        
        with open(self.graph_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


# 全局实例
_knowledge_graph = None

def get_knowledge_graph() -> KnowledgeGraph:
    """获取全局知识图谱实例"""
    global _knowledge_graph
    if _knowledge_graph is None:
        _knowledge_graph = KnowledgeGraph()
    return _knowledge_graph


if __name__ == "__main__":
    # 测试代码
    kg = KnowledgeGraph()
    
    # 添加实体
    kg.add_entity("python", "tool", {"description": "Python编程语言"})
    kg.add_entity("write_file", "tool", {"description": "写文件工具"})
    kg.add_entity("file_not_found", "error", {"description": "文件未找到错误"})
    kg.add_entity("check_file_exists", "solution", {"description": "检查文件是否存在"})
    kg.add_entity("create_script", "task", {"description": "创建脚本任务"})
    
    # 添加关系
    kg.add_relation("create_script", "uses", "python")
    kg.add_relation("create_script", "uses", "write_file")
    kg.add_relation("write_file", "may_cause", "file_not_found")
    kg.add_relation("check_file_exists", "solves", "file_not_found")
    kg.add_relation("create_script", "requires", "python")
    
    # 查询
    print("=== 统计信息 ===")
    stats = kg.get_statistics()
    print(f"实体数: {stats['total_entities']}")
    print(f"关系数: {stats['total_relations']}")
    print(f"实体类型: {stats['entity_types']}")
    print(f"关系类型: {stats['relation_types']}")
    
    print("\n=== 查找工具类实体 ===")
    tools = kg.find_entities(type="tool")
    for tool in tools:
        print(f"- {tool.id}: {tool.properties.get('description')}")
    
    print("\n=== 查找create_script的邻居 ===")
    neighbors = kg.get_neighbors("create_script")
    for neighbor, relation in neighbors:
        print(f"- {relation.relation_type} -> {neighbor.id}")
    
    print("\n=== 推理新关系 ===")
    inferred = kg.infer_relations("create_script")
    for source, rel_type, target in inferred:
        print(f"- {source} --[{rel_type}]--> {target}")
    
    print("\n" + kg.visualize("create_script", depth=2))
