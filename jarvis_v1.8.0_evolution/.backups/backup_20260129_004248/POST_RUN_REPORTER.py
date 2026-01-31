"""
JARVIS 任务报告生成器 - Manus 风格
使用 LLM 智能分析任务执行情况，生成有洞察力的报告
"""
import json
import datetime
from pathlib import Path

from llm import chat
from safe_io import safe_read_json, safe_write

_ROOT = Path(__file__).parent

# 数据文件
STATE_FILE = _ROOT / "STATE.json"
PLAN_FILE = _ROOT / "PLAN.json"
ERROR_FILE = _ROOT / "ERRORS.json"
EVENT_FILE = _ROOT / "EVENTS.json"
MEMORY_FILE = _ROOT / "CHAT_MEMORY.json"

# 输出文件
OUTPUT_MD = _ROOT / "POST_RUN_REPORT.md"


def load(p, default):
    """安全加载 JSON 文件"""
    return safe_read_json(str(p), default=default)


def collect_context(user_goal: str = None, task_result: str = None) -> dict:
    """收集任务执行的完整上下文"""
    state = load(STATE_FILE, {})
    plan = load(PLAN_FILE, {})
    errors = load(ERROR_FILE, {})
    events = load(EVENT_FILE, {}).get("events", [])
    memory = load(MEMORY_FILE, {})

    context = {
        "user_goal": user_goal or state.get("current_goal", "未知目标"),
        "task_result": task_result,
        "completed_steps": state.get("completed_steps", []),
        "plan_steps": plan.get("steps", []),
        "understanding": plan.get("understanding", ""),
        "errors": errors.get("history", [])[-10:],
        "recent_events": [],
        "recent_history": memory.get("history", [])[-3:],
    }

    for e in events[-30:]:
        if e["type"] in ("error", "result", "status", "confirm"):
            context["recent_events"].append({
                "type": e["type"],
                "message": e["message"][:200]
            })

    return context


def generate_smart_report(context: dict) -> str:
    """使用 LLM 生成 Manus 风格的智能报告"""
    prompt = f"""你是一个专业的任务报告生成器。请根据以下任务执行信息，生成一份 Manus 风格的结构化报告。

## 任务信息

**用户目标**: {context['user_goal']}
**任务理解**: {context['understanding']}

**完成的步骤**:
{json.dumps(context['completed_steps'], ensure_ascii=False, indent=2) if context['completed_steps'] else '无'}

**执行结果**:
{context['task_result'] or '无具体结果'}

**错误记录**:
{json.dumps(context['errors'], ensure_ascii=False, indent=2) if context['errors'] else '无错误'}

## 报告要求

请生成一份专业的任务报告，包含以下部分：

1. **任务完成总结**（一句话概括）

2. **执行状态**
   - 是否完成
   - 完成了哪些步骤

3. **问题现象**（如果有错误）

4. **根因分析**（如果有错误）

5. **核心原则**（重要！）
   用对比的方式提炼：
   
   错误理解（❌）
   [描述错误的理解方式]
   
   正确理解（✅）
   [描述正确的理解方式]

6. **修复方案**（如果涉及修复）
   - Before：[修复前]
   - After：[修复后]

7. **产品/交互意义**

8. **工程收尾**

请直接输出 Markdown 格式的报告。"""

    try:
        report = chat(prompt)
        return report
    except Exception as e:
        return generate_basic_report(context)


def generate_basic_report(context: dict) -> str:
    """生成基础报告（LLM 不可用时的后备方案）"""
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    md = []
    md.append("# 📋 任务执行报告")
    md.append("")
    md.append(f"**生成时间**：{now}")
    md.append("")
    md.append("## 任务概述")
    md.append(f"**用户目标**：{context['user_goal']}")
    md.append(f"**执行状态**：{'✅ 完成' if context['completed_steps'] else '⚠️ 进行中'}")
    md.append("")
    
    if context['completed_steps']:
        md.append("## 完成步骤")
        for step in context['completed_steps']:
            md.append(f"- ✅ {step}")
        md.append("")
    
    if context['errors']:
        md.append("## 问题记录")
        for err in context['errors']:
            md.append(f"- ❌ {err.get('step', '未知')}: {err.get('error', '未知错误')}")
        md.append("")
    
    if context['task_result']:
        md.append("## 执行结果")
        md.append(context['task_result'])
        md.append("")
    
    md.append("---")
    md.append(f"_报告生成时间：{now}_")
    
    return "\n".join(md)


def render(user_goal: str = None, task_result: str = None, use_llm: bool = True) -> str:
    """生成任务报告"""
    context = collect_context(user_goal, task_result)
    
    if use_llm:
        report_content = generate_smart_report(context)
    else:
        report_content = generate_basic_report(context)
    
    header = f"""<!--
报告生成时间: {datetime.datetime.now().isoformat()}
用户目标: {context['user_goal']}
-->

"""
    
    safe_write(str(OUTPUT_MD), header + report_content)
    return str(OUTPUT_MD)


def get_latest_report() -> str:
    """获取最新报告内容"""
    try:
        with open(OUTPUT_MD, "r", encoding="utf-8") as f:
            content = f.read()
            if content.startswith("<!--"):
                end_comment = content.find("-->")
                if end_comment != -1:
                    content = content[end_comment + 3:].strip()
            return content
    except (FileNotFoundError, IOError):
        return "暂无报告"


if __name__ == "__main__":
    report_path = render(
        user_goal="测试 Manus 风格报告生成",
        task_result="报告生成器已升级",
        use_llm=True
    )
    print(f"报告已生成: {report_path}")
