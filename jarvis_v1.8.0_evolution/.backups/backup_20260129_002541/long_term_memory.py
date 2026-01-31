"""
JARVIS 长期记忆系统
突破 LLM 上下文窗口限制，利用本地文件系统作为外部记忆
"""
import json
import datetime
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from safe_io import safe_write_json, safe_read_json, safe_write

_ROOT = Path(__file__).parent

# 记忆目录结构
MEMORY_DIR = _ROOT / "memory"
RULES_DIR = MEMORY_DIR / "rules"
KNOWLEDGE_DIR = MEMORY_DIR / "knowledge"
EXPERIENCE_DIR = MEMORY_DIR / "experience"
CONTEXT_DIR = MEMORY_DIR / "context"
MEMORY_INDEX = MEMORY_DIR / "index.json"


def init_memory_system():
    """初始化记忆系统目录结构"""
    for dir_path in [MEMORY_DIR, RULES_DIR, KNOWLEDGE_DIR, EXPERIENCE_DIR, CONTEXT_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    if not MEMORY_INDEX.exists():
        safe_write_json(str(MEMORY_INDEX), {
            "rules": [], "knowledge": [], "experience": [], "context": [],
            "created_at": datetime.datetime.now().isoformat(),
            "last_updated": datetime.datetime.now().isoformat()
        })


def _update_index(category: str, entry: dict):
    """更新索引"""
    index = safe_read_json(str(MEMORY_INDEX), default={
        "rules": [], "knowledge": [], "experience": [], "context": []
    })
    
    if category not in index:
        index[category] = []
    
    index[category].append(entry)
    index["last_updated"] = datetime.datetime.now().isoformat()
    
    if len(index[category]) > 100:
        index[category] = index[category][-100:]
    
    safe_write_json(str(MEMORY_INDEX), index)


# ==================== 规则管理 ====================

def save_rule(name: str, content: str, category: str = "general") -> str:
    """保存规则到长期记忆"""
    init_memory_system()
    
    filename = f"{category}_{name}.md"
    filepath = RULES_DIR / filename
    
    header = f"""# {name}

**类别**: {category}
**创建时间**: {datetime.datetime.now().isoformat()}

---

"""
    safe_write(str(filepath), header + content)
    
    _update_index("rules", {
        "name": name, "category": category, "file": filename,
        "created_at": datetime.datetime.now().isoformat()
    })
    
    return str(filepath)


def get_rule(name: str, category: str = "general") -> Optional[str]:
    """获取指定规则"""
    filepath = RULES_DIR / f"{category}_{name}.md"
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    return None


def list_rules() -> List[Dict]:
    """列出所有规则"""
    index = safe_read_json(str(MEMORY_INDEX), default={})
    return index.get("rules", [])


def get_all_rules() -> str:
    """获取所有规则的内容"""
    rules = []
    if RULES_DIR.exists():
        for rule_file in RULES_DIR.glob("*.md"):
            with open(rule_file, "r", encoding="utf-8") as f:
                rules.append(f.read())
    return "\n\n---\n\n".join(rules) if rules else "暂无规则"


# ==================== 知识管理 ====================

def save_knowledge(topic: str, content: str, tags: List[str] = None) -> str:
    """保存项目知识"""
    init_memory_system()
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{topic.replace(' ', '_')}.md"
    filepath = KNOWLEDGE_DIR / filename
    
    tags_str = ", ".join(tags) if tags else "无"
    header = f"""# {topic}

**标签**: {tags_str}
**记录时间**: {datetime.datetime.now().isoformat()}

---

"""
    safe_write(str(filepath), header + content)
    
    _update_index("knowledge", {
        "topic": topic, "tags": tags or [], "file": filename,
        "created_at": datetime.datetime.now().isoformat()
    })
    
    return str(filepath)


def search_knowledge(keyword: str) -> List[Dict]:
    """搜索知识库"""
    results = []
    if KNOWLEDGE_DIR.exists():
        for knowledge_file in KNOWLEDGE_DIR.glob("*.md"):
            with open(knowledge_file, "r", encoding="utf-8") as f:
                content = f.read()
                if keyword.lower() in content.lower():
                    results.append({
                        "file": knowledge_file.name,
                        "preview": content[:200] + "..." if len(content) > 200 else content
                    })
    return results


def get_recent_knowledge(limit: int = 5) -> str:
    """获取最近的知识条目"""
    if not KNOWLEDGE_DIR.exists():
        return "暂无知识记录"
    
    files = sorted(KNOWLEDGE_DIR.glob("*.md"), key=os.path.getmtime, reverse=True)[:limit]
    contents = []
    for f in files:
        with open(f, "r", encoding="utf-8") as file:
            contents.append(file.read())
    
    return "\n\n---\n\n".join(contents) if contents else "暂无知识记录"


# ==================== 经验管理 ====================

def save_experience(title: str, problem: str, solution: str, lesson: str) -> str:
    """保存经验教训"""
    init_memory_system()
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{title.replace(' ', '_')}.md"
    filepath = EXPERIENCE_DIR / filename
    
    content = f"""# {title}

**记录时间**: {datetime.datetime.now().isoformat()}

## 问题描述
{problem}

## 解决方案
{solution}

## 经验教训
{lesson}
"""
    safe_write(str(filepath), content)
    
    _update_index("experience", {
        "title": title, "file": filename,
        "created_at": datetime.datetime.now().isoformat()
    })
    
    return str(filepath)


def get_relevant_experience(keywords: List[str]) -> str:
    """根据关键词获取相关经验"""
    results = []
    if EXPERIENCE_DIR.exists():
        for exp_file in EXPERIENCE_DIR.glob("*.md"):
            with open(exp_file, "r", encoding="utf-8") as f:
                content = f.read()
                for kw in keywords:
                    if kw.lower() in content.lower():
                        results.append(content)
                        break
    
    return "\n\n---\n\n".join(results[:3]) if results else "暂无相关经验"


# ==================== 上下文快照 ====================

def save_context_snapshot(task_id: str, context: Dict[str, Any]) -> str:
    """保存任务上下文快照"""
    init_memory_system()
    
    filename = f"{task_id}.json"
    filepath = CONTEXT_DIR / filename
    
    context["saved_at"] = datetime.datetime.now().isoformat()
    safe_write_json(str(filepath), context)
    
    _update_index("context", {
        "task_id": task_id, "file": filename, "saved_at": context["saved_at"]
    })
    
    return str(filepath)


def load_context_snapshot(task_id: str) -> Optional[Dict]:
    """加载任务上下文快照"""
    filepath = CONTEXT_DIR / f"{task_id}.json"
    if filepath.exists():
        return safe_read_json(str(filepath), default=None)
    return None


def clear_context_snapshot(task_id: str) -> bool:
    """清除任务上下文快照"""
    filepath = CONTEXT_DIR / f"{task_id}.json"
    if filepath.exists():
        filepath.unlink()
        return True
    return False


# ==================== 记忆摘要 ====================

def get_memory_summary() -> str:
    """获取记忆摘要"""
    init_memory_system()
    
    summary = []
    
    rules = list_rules()
    if rules:
        summary.append("## 已知规则")
        for r in rules[-5:]:
            summary.append(f"- [{r['category']}] {r['name']}")
    
    index = safe_read_json(str(MEMORY_INDEX), default={})
    knowledge = index.get("knowledge", [])
    if knowledge:
        summary.append("\n## 最近知识")
        for k in knowledge[-5:]:
            summary.append(f"- {k['topic']} (标签: {', '.join(k.get('tags', []))})")
    
    experience = index.get("experience", [])
    if experience:
        summary.append("\n## 最近经验")
        for e in experience[-5:]:
            summary.append(f"- {e['title']}")
    
    return "\n".join(summary) if summary else "暂无长期记忆"


def inject_memory_to_prompt(base_prompt: str) -> str:
    """将长期记忆注入到 prompt 中"""
    rules = get_all_rules()
    memory_summary = get_memory_summary()
    
    memory_section = f"""
## 长期记忆

### 规则和约束
{rules}

### 记忆摘要
{memory_summary}

---

"""
    return memory_section + base_prompt


# ==================== 初始化默认规则 ====================

def setup_default_rules():
    """设置默认规则"""
    init_memory_system()
    
    save_rule(
        name="delete_confirmation",
        content="""删除任何文件之前必须获得用户确认。

流程：
1. 用户请求删除文件
2. 将文件加入待确认删除队列
3. 向用户展示待删除文件信息
4. 等待用户明确确认
5. 确认后才执行删除

禁止：
- 未经确认直接删除文件
- 批量删除时跳过确认
""",
        category="security"
    )
    
    save_rule(
        name="persistent_execution",
        content="""任务执行原则：不达目的不罢休。

行为准则：
1. 遇到错误时，先分析原因，尝试不同方案
2. 一个方案失败，自动切换到备选方案
3. 最多重试 5 次后，向用户报告并请求指导
4. 只有在以下情况才停止：
   - 任务成功完成
   - 用户明确要求停止
   - 所有方案都已尝试且失败

禁止：
- 遇到第一个错误就放弃
- 不尝试替代方案就报告失败
""",
        category="workflow"
    )
    
    print("默认规则已设置")


if __name__ == "__main__":
    setup_default_rules()
    print("\n记忆摘要:")
    print(get_memory_summary())
