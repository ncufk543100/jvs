"""
错误日志管理器 (Error Logger)
混合使用TXT和知识图谱，兼顾快速查看和深度分析

核心功能：
1. TXT日志：快速记录和查看最近的错误
2. 知识图谱：存储错误关系，支持分析和推理
3. 错误统计：分析错误模式和频率
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from knowledge_graph import get_knowledge_graph

class ErrorLogger:
    """混合错误日志管理器"""
    
    def __init__(self, log_file: str = "/home/ubuntu/jarvis/data/error_log.txt"):
        self.log_file = log_file
        self.kg = get_knowledge_graph()
        
        # 确保日志目录存在
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # 初始化日志文件
        if not os.path.exists(log_file):
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write("# JARVIS 错误日志\n")
                f.write(f"# 创建时间: {datetime.now().isoformat()}\n\n")
    
    def log_error(
        self,
        error_type: str,
        error_msg: str,
        task_id: str = None,
        phase_id: int = None,
        phase_title: str = None,
        tool_name: str = None,
        context: Dict = None
    ) -> str:
        """
        记录错误（同时写入TXT和知识图谱）
        
        Args:
            error_type: 错误类型（file_error, permission_error, timeout等）
            error_msg: 错误消息
            task_id: 任务ID
            phase_id: 阶段ID
            phase_title: 阶段标题
            tool_name: 工具名称
            context: 额外上下文信息
        
        Returns:
            str: 错误ID
        """
        timestamp = datetime.now().isoformat()
        error_id = f"error_{timestamp.replace(':', '-').replace('.', '-')}"
        
        # 1. 写入TXT日志（人类可读）
        self._write_txt_log(
            error_id, error_type, error_msg, timestamp,
            task_id, phase_id, phase_title, tool_name, context
        )
        
        # 2. 写入知识图谱（机器分析）
        self._write_to_kg(
            error_id, error_type, error_msg, timestamp,
            task_id, phase_id, phase_title, tool_name, context
        )
        
        return error_id
    
    def _write_txt_log(
        self,
        error_id: str,
        error_type: str,
        error_msg: str,
        timestamp: str,
        task_id: str,
        phase_id: int,
        phase_title: str,
        tool_name: str,
        context: Dict
    ):
        """写入TXT日志"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"## [{timestamp}] {error_type}\n")
            f.write(f"**错误ID**: {error_id}\n")
            f.write(f"**消息**: {error_msg}\n")
            
            if task_id:
                f.write(f"**任务ID**: {task_id}\n")
            
            if phase_id and phase_title:
                f.write(f"**阶段**: {phase_id} - {phase_title}\n")
            
            if tool_name:
                f.write(f"**工具**: {tool_name}\n")
            
            if context:
                f.write(f"**上下文**: {json.dumps(context, ensure_ascii=False, indent=2)}\n")
            
            f.write("\n---\n\n")
    
    def _write_to_kg(
        self,
        error_id: str,
        error_type: str,
        error_msg: str,
        timestamp: str,
        task_id: str,
        phase_id: int,
        phase_title: str,
        tool_name: str,
        context: Dict
    ):
        """写入知识图谱"""
        # 添加错误实体
        self.kg.add_entity(
            error_id,
            "error",
            {
                "type": error_type,
                "message": error_msg,
                "timestamp": timestamp,
                "phase_id": phase_id,
                "phase_title": phase_title,
                "tool_name": tool_name,
                "context": context or {}
            }
        )
        
        # 建立关系
        if task_id:
            # 确保任务实体存在
            if not self.kg.get_entity(task_id):
                self.kg.add_entity(task_id, "task", {"id": task_id})
            self.kg.add_relation(task_id, "encountered", error_id)
        
        if tool_name:
            tool_id = f"tool_{tool_name}"
            if not self.kg.get_entity(tool_id):
                self.kg.add_entity(tool_id, "tool", {"name": tool_name})
            self.kg.add_relation(tool_id, "caused", error_id)
    
    def get_recent_errors(self, limit: int = 10) -> str:
        """
        获取最近的错误（从TXT日志）
        
        Args:
            limit: 返回的错误数量
        
        Returns:
            str: 最近的错误日志
        """
        if not os.path.exists(self.log_file):
            return "暂无错误日志"
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 找到最后N个错误块
        error_blocks = []
        current_block = []
        
        for line in lines:
            if line.startswith("## ["):
                if current_block:
                    error_blocks.append(''.join(current_block))
                current_block = [line]
            elif current_block:
                current_block.append(line)
        
        if current_block:
            error_blocks.append(''.join(current_block))
        
        # 返回最后N个
        recent = error_blocks[-limit:]
        return ''.join(recent) if recent else "暂无错误日志"
    
    def analyze_error_patterns(self) -> Dict:
        """
        分析错误模式（使用知识图谱）
        
        Returns:
            Dict: {
                total_errors: int,
                by_type: Dict[str, int],
                by_tool: Dict[str, int],
                most_common: str
            }
        """
        # 获取所有错误实体
        all_entities = self.kg.entities
        errors = {
            eid: entity
            for eid, entity in all_entities.items()
            if entity.type == "error"
        }
        
        if not errors:
            return {
                "total_errors": 0,
                "by_type": {},
                "by_tool": {},
                "most_common": None
            }
        
        # 按类型统计
        by_type = {}
        by_tool = {}
        
        for error_id, error in errors.items():
            props = error.properties
            
            # 按错误类型
            error_type = props.get("type", "unknown")
            by_type[error_type] = by_type.get(error_type, 0) + 1
            
            # 按工具
            tool_name = props.get("tool_name")
            if tool_name:
                by_tool[tool_name] = by_tool.get(tool_name, 0) + 1
        
        # 找出最常见的错误类型
        most_common = max(by_type.items(), key=lambda x: x[1])[0] if by_type else None
        
        return {
            "total_errors": len(errors),
            "by_type": by_type,
            "by_tool": by_tool,
            "most_common": most_common
        }
    
    def find_related_errors(self, error_id: str) -> List[Dict]:
        """
        查找相关错误（使用知识图谱推理）
        
        Args:
            error_id: 错误ID
        
        Returns:
            List[Dict]: 相关错误列表
        """
        related = []
        
        # 1. 找到同一任务的其他错误
        task_relations = self.kg.query_relations(predicate="encountered")
        for task_id, _, err_id in task_relations:
            if err_id == error_id:
                # 找到这个任务的所有错误
                for t_id, _, other_err_id in task_relations:
                    if t_id == task_id and other_err_id != error_id:
                        error_entity = self.kg.get_entity(other_err_id)
                        if error_entity:
                            related.append({
                                "error_id": other_err_id,
                                "relation": "same_task",
                                "details": error_entity.properties
                            })
        
        # 2. 找到同一工具引起的其他错误
        tool_relations = self.kg.query_relations(predicate="caused")
        for tool_id, _, err_id in tool_relations:
            if err_id == error_id:
                # 找到这个工具的所有错误
                for t_id, _, other_err_id in tool_relations:
                    if t_id == tool_id and other_err_id != error_id:
                        error_entity = self.kg.get_entity(other_err_id)
                        if error_entity:
                            related.append({
                                "error_id": other_err_id,
                                "relation": "same_tool",
                                "details": error_entity.properties
                            })
        
        return related
    
    def generate_error_report(self) -> str:
        """
        生成错误分析报告
        
        Returns:
            str: Markdown格式的报告
        """
        analysis = self.analyze_error_patterns()
        
        report = "# JARVIS 错误分析报告\n\n"
        report += f"**生成时间**: {datetime.now().isoformat()}\n\n"
        
        report += f"## 总体统计\n\n"
        report += f"- **总错误数**: {analysis['total_errors']}\n"
        report += f"- **最常见错误类型**: {analysis['most_common']}\n\n"
        
        report += f"## 按错误类型\n\n"
        for error_type, count in sorted(analysis['by_type'].items(), key=lambda x: x[1], reverse=True):
            report += f"- **{error_type}**: {count} 次\n"
        
        report += f"\n## 按工具\n\n"
        for tool_name, count in sorted(analysis['by_tool'].items(), key=lambda x: x[1], reverse=True):
            report += f"- **{tool_name}**: {count} 次\n"
        
        report += f"\n## 最近的错误\n\n"
        report += self.get_recent_errors(limit=5)
        
        return report


# 全局实例
_logger = None

def get_error_logger() -> ErrorLogger:
    """获取全局错误日志管理器实例"""
    global _logger
    if _logger is None:
        _logger = ErrorLogger()
    return _logger


if __name__ == "__main__":
    # 测试代码
    logger = ErrorLogger()
    
    # 记录几个测试错误
    logger.log_error(
        error_type="file_error",
        error_msg="文件不存在: /tmp/test.txt",
        task_id="task_001",
        phase_id=2,
        phase_title="执行实施",
        tool_name="read_file"
    )
    
    logger.log_error(
        error_type="permission_error",
        error_msg="没有写入权限: /etc/test.conf",
        task_id="task_001",
        phase_id=3,
        phase_title="配置部署",
        tool_name="write_file"
    )
    
    logger.log_error(
        error_type="timeout",
        error_msg="命令执行超时",
        task_id="task_002",
        phase_id=1,
        phase_title="环境准备",
        tool_name="run_shell"
    )
    
    # 查看最近的错误
    print("=== 最近的错误 ===")
    print(logger.get_recent_errors(limit=3))
    
    # 分析错误模式
    print("\n=== 错误模式分析 ===")
    analysis = logger.analyze_error_patterns()
    print(f"总错误数: {analysis['total_errors']}")
    print(f"按类型: {analysis['by_type']}")
    print(f"按工具: {analysis['by_tool']}")
    print(f"最常见: {analysis['most_common']}")
    
    # 生成报告
    print("\n=== 错误报告 ===")
    print(logger.generate_error_report())
