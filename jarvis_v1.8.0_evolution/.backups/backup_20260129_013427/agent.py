"""
JARVIS 智能代理模块 v3.0

核心特性：
- 持续执行直到目标达成（不达目的不罢休）
- Agent 主权判断（可拒绝执行）
- 结论性判断输出（从分析到定性）
- 用户偏好系统（越用越懂你）
- 长期记忆系统集成
- Manus 风格任务报告
"""
import json
import threading
import re
import time
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any

from llm import think, chat
from executor import execute, get_available_tools
from run_lock import acquire, release
from safe_io import safe_write_json, safe_read_json
from event_bus import emit
from POST_RUN_REPORTER import render as generate_report
from long_term_memory import (
    get_all_rules, 
    get_memory_summary, 
    save_experience,
    save_context_snapshot,
    load_context_snapshot,
    clear_context_snapshot
)

# 导入三大核心功能
from agent_sovereignty import (
    evaluate_action,
    quick_assess,
    should_refuse,
    needs_confirmation,
    generate_refusal_message,
    AgentJudgment,
    JudgmentType,
    RiskLevel
)
from execution_profile import get_current_profile, ProfileContext
from agent_conclusion import (
    generate_conclusion,
    AgentConclusion,
    ProblemNature,
    FixApproach
)
from user_preferences import (
    load_preferences,
    save_preferences,
    update_preference,
    learn_preference,
    get_preference,
    should_confirm,
    apply_preferences_to_decision,
    get_preferences_summary,
    infer_preference_from_action
)

# 文件路径
_ROOT = Path(__file__).parent
STATE_FILE = _ROOT / "STATE.json"
PLAN_FILE = _ROOT / "PLAN.json"
ERROR_FILE = _ROOT / "ERRORS.json"
MEMORY_FILE = _ROOT / "CHAT_MEMORY.json"
JUDGMENT_FILE = _ROOT / "AGENT_JUDGMENTS.json"

# 配置
STEP_TIMEOUT = 120  # 单步超时（秒）
MAX_RETRIES = 5     # 最大重试次数
MAX_ITERATIONS = 50 # 最大迭代次数


class StepTimeoutError(Exception):
    """步骤执行超时异常"""
    pass


class AgentRefusalError(Exception):
    """Agent 拒绝执行异常"""
    def __init__(self, judgment: AgentJudgment):
        self.judgment = judgment
        super().__init__(judgment.reasoning)


def load_json(path: Path, default=None):
    """安全加载 JSON 文件"""
    return safe_read_json(str(path), default=default or {})


def save_memory(memory: dict) -> None:
    """保存对话记忆（无数量限制）"""
    safe_write_json(str(MEMORY_FILE), memory)


def load_memory() -> dict:
    """加载对话记忆"""
    default = {"history": [], "context": {}}
    return safe_read_json(str(MEMORY_FILE), default=default)


def save_judgment(judgment_data: dict) -> None:
    """保存 Agent 判断记录"""
    judgments = safe_read_json(str(JUDGMENT_FILE), default={"history": []})
    judgments["history"].append({
        **judgment_data,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })
    # 只保留最近 100 条
    if len(judgments["history"]) > 100:
        judgments["history"] = judgments["history"][-100:]
    safe_write_json(str(JUDGMENT_FILE), judgments)


def run_with_timeout(func, timeout: int):
    """线程安全的超时执行"""
    result = [None]
    exception = [None]

    def target():
        try:
            result[0] = func()
        except Exception as e:
            exception[0] = e

    thread = threading.Thread(target=target)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        raise StepTimeoutError(f"步骤执行超时（{timeout}秒）")

    if exception[0]:
        raise exception[0]

    return result[0]


def create_dynamic_plan(goal: str, memory: dict, failed_approaches: List[str] = None) -> dict:
    """根据用户目标动态创建执行计划"""
    available_tools = get_available_tools()
    tools_desc = "\n".join([f"- {name}: {desc}" for name, desc in available_tools.items()])
    
    # 获取历史上下文
    history_context = ""
    if memory.get("history"):
        recent = memory["history"][-5:]
        history_context = "\n".join([
            f"用户: {h['user']}\n助手: {h['assistant']}" 
            for h in recent
        ])
    
    # 获取失败方案
    failed_context = ""
    if failed_approaches:
        failed_context = f"\n\n已失败的方案（请避免）:\n" + "\n".join(f"- {a}" for a in failed_approaches)
    
    # 获取长期记忆
    memory_context = get_memory_summary()
    
    # 获取用户偏好
    preferences_context = get_preferences_summary()
    
    prompt = f"""你是JARVIS，一个智能AI助理。你必须严格遵循"分析→规划→实施"的流程。

## 用户目标
{goal}

## 核心原则
1. **先分析，后规划，再实施** - 永远不要跳过分析阶段
2. **遇到错误时，分析原因并调整策略** - 不要重复相同的失败操作
3. **缺少依赖时，自动创建** - 遇到"模块不存在"错误，应该创建该模块
4. **每个步骤必须包含具体参数** - 不要生成空的params

## 任务执行流程

### 阶段1：深度分析（必须执行）
- 理解用户的真实意图
- 分析当前状态和能力差距
- 识别需要的资源和依赖
- 列出可能的障碍

### 阶段2：制定计划
- 将目标分解为具体步骤
- 每个步骤必须包含：
  * tool: 工具名称
  * params: 具体参数（必须填写，不能为空）
  * expected: 预期结果
- 考虑依赖关系和执行顺序

### 阶段3：逐步实施
- 按顺序执行每个步骤
- 验证每步结果
- 遇到错误时，分析并调整

## 可用工具
{tools_desc}

## 历史对话
{history_context if history_context else "无"}

## 长期记忆
{memory_context}

## 用户偏好
{preferences_context}
{failed_context}

## 错误处理规则
- **模块不存在** → 使用write_file创建该模块
- **参数缺失** → 查看工具描述，补充具体参数
- **测试失败** → 分析失败原因，修复代码
- **连续3次失败** → 重新分析问题，换方案

## 重要规则
1. 删除任何文件必须使用 delete_file 工具，需要用户确认
2. 禁止批量修改文件，必须逐个文件处理
3. 高风险操作需要先评估再执行
4. 根据用户偏好调整执行方式
5. **工具请示机制**：当你发现缺少某个工具时，必须使用 request_tool_installation 请示主人，不可自行安装
6. **代码规范**：生成任何代码时，不要写注释，保持代码简洁

## 禁止行为
- ❌ 跳过分析阶段直接实施
- ❌ 重复相同的失败操作
- ❌ 生成空参数的计划（params: {{}}）
- ❌ 遇到"模块不存在"错误只重试不创建

## 任务
**第一步：判断请求类型**
- 如果用户只是问候、闲聊、询问你的能力、让你自我介绍，**必须返回空的 steps 数组 []**
- 如果用户需要你执行具体操作（读写文件、运行命令、扫描项目等），才制定执行计划

**第二步：制定计划**
- 对于纯对话：steps 必须为空数组 []
- 对于具体任务：制定详细执行计划

**第三步：填写具体参数**
- params 不能为空，必须填写具体的参数值
- 例如：self_modify_write 需要 filename 和 content 参数
- 例如：read_file 需要 path 参数
- 例如：scan_files 需要 path 参数
- 如果不确定参数值，使用占位符如 "<需要确定>" 并在 description 中说明

请用 JSON 格式回复：
{{
    "understanding": "你对用户目标的理解",
    "approach": "你的方案名称",
    "risk_assessment": "风险评估: low/medium/high",
    "steps": [
        {{"tool": "工具名", "params": {{"param_name": "param_value"}}, "description": "步骤描述"}}
    ]
}}
"""
    
    try:
        response = think(prompt)
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        print(f"[PLAN] 生成计划失败: {e}")
    
    return {"understanding": goal, "approach": "默认方案", "steps": []}


def evaluate_step_before_execution(
    tool: str, 
    params: dict, 
    goal: str,
    context: dict = None
) -> AgentJudgment:
    """
    在执行步骤前进行 Agent 主权判断
    
    这是 Agent 从"工具"升级为"代理人"的关键
    """
    action_desc = f"使用 {tool} 工具，参数: {json.dumps(params, ensure_ascii=False)}"
    
    # 快速评估（不调用 LLM）
    can_proceed, reason = quick_assess(action_desc)
    if not can_proceed:
        return AgentJudgment(
            judgment_type=JudgmentType.REFUSE,
            risk_level=RiskLevel.CRITICAL,
            reasoning=reason,
            conclusion="操作被安全规则禁止",
            risks=[reason],
            alternatives=[],
            recommendation="请使用更安全的方式完成任务",
            confidence=1.0
        )
    
    # 获取用户偏好
    prefs = load_preferences()
    user_preferences = {
        "risk_tolerance": prefs.risk_tolerance,
        "prefer_structural_fix": prefs.prefer_structural_fix,
        "batch_operations_forbidden": prefs.batch_operations_forbidden,
    }
    
    # 获取当前执行剖面
    profile_context = get_current_profile()
    
    # 完整评估（根据profile选择评估策略）
    judgment = evaluate_action(
        action=action_desc,
        goal=goal,
        context=context,
        user_preferences=user_preferences,
        profile_context=profile_context
    )
    
    # 保存判断记录
    save_judgment({
        "tool": tool,
        "params": params,
        "goal": goal,
        "judgment": judgment.to_dict()
    })
    
    return judgment


def evaluate_result(goal: str, results: List[str], errors: List[str]) -> dict:
    """评估执行结果是否达成目标"""
    prompt = f"""评估以下执行结果是否达成了用户目标。

用户目标: {goal}

执行结果:
{chr(10).join(results) if results else "无"}

错误记录:
{chr(10).join(errors) if errors else "无"}

请用 JSON 格式回复：
{{
    "success": true/false,
    "reason": "判断原因",
    "suggestion": "如果失败，建议下一步怎么做"
}}
"""
    
    try:
        response = think(prompt)
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        print(f"[EVAL] 评估失败: {e}")
    
    if errors:
        return {
            "success": False,
            "reason": "执行过程中有错误",
            "suggestion": "分析错误原因，尝试其他方案"
        }
    return {"success": True, "reason": "执行完成无错误", "suggestion": ""}


def run_agent(goal: str) -> str:
    """
    运行智能代理 - 持续执行直到目标达成
    
    v3.0 新增：
    - 执行前进行 Agent 主权判断
    - 根据用户偏好调整行为
    - 生成结论性判断
    """
    acquire()
    task_id = str(uuid.uuid4())[:8]
    
    task_result = None
    failed_approaches = []
    all_results = []
    all_errors = []
    all_judgments = []
    iteration = 0
    
    try:
        emit("user", goal)
        emit("status", "🚀 开始执行任务，将持续运行直到目标达成...")
        
        # 加载用户偏好
        prefs = load_preferences()
        emit("status", f"📋 已加载用户偏好 (风险容忍度: {prefs.risk_tolerance})")
        
        memory = load_memory()
        
        state = load_json(STATE_FILE)
        state["current_goal"] = goal
        state["task_id"] = task_id
        state["completed_steps"] = []
        state["status"] = "running"
        state["agent_version"] = "3.0"
        safe_write_json(str(STATE_FILE), state)
        
        while iteration < MAX_ITERATIONS:
            iteration += 1
            emit("status", f"📋 第 {iteration} 次尝试...")
            
            emit("thinking", f"🤔 正在分析任务并制定执行计划...")
            plan = create_dynamic_plan(goal, memory, failed_approaches)
            emit("thinking", f"📋 计划制定完成: {plan.get('approach', '未知方案')}")
            
            understanding = plan.get("understanding", goal)
            approach = plan.get("approach", f"方案{iteration}")
            steps = plan.get("steps", [])
            risk_assessment = plan.get("risk_assessment", "medium")
            
            emit("confirm", f"方案: {approach}\n理解: {understanding}\n风险: {risk_assessment}")
            
            save_context_snapshot(task_id, {
                "goal": goal,
                "iteration": iteration,
                "approach": approach,
                "failed_approaches": failed_approaches
            })
            
            plan_data = {
                "goal": goal,
                "understanding": understanding,
                "approach": approach,
                "iteration": iteration,
                "risk_assessment": risk_assessment,
                "steps": [{"id": s.get("description", s.get("tool")), "tool": s.get("tool"), "status": "pending"} for s in steps]
            }
            safe_write_json(str(PLAN_FILE), plan_data)
            
            # 如果没有步骤（闲聊）
            if not steps:
                response = chat(
                    f"用户说: {goal}\n\n"
                    "请友好地回复用户。如果用户在询问你的能力，告诉他们你可以: "
                    "扫描项目、读写文件、执行命令、分析代码、查看Git状态、删除文件（需确认）、"
                    "调用微信开发者工具等。\n\n"
                    "重要：我是一个有主权的代理人，会根据你的偏好工作，"
                    "对于高风险操作我会先评估再执行，必要时会拒绝执行。"
                )
                emit("result", response)
                task_result = response
                
                # 从用户输入学习偏好
                infer_preference_from_action(goal, response)
                
                memory["history"].append({"user": goal, "assistant": response})
                save_memory(memory)
                
                generate_report(user_goal=goal, task_result=task_result)
                emit("done", "对话完成")
                
                state["status"] = "completed"
                safe_write_json(str(STATE_FILE), state)
                clear_context_snapshot(task_id)
                return "DONE"
            
            # 执行步骤
            step_results = []
            step_errors = []
            errors_data = load_json(ERROR_FILE)
            agent_refused = False
            
            for i, step in enumerate(steps):
                tool = step.get("tool", "")
                params = step.get("params", {})
                desc = step.get("description", f"执行 {tool}")
                
                emit("status", f"步骤 {i+1}/{len(steps)}: {desc}")
                
                # === Agent 主权判断 ===
                emit("status", f"🔍 评估步骤安全性...")
                judgment = evaluate_step_before_execution(
                    tool=tool,
                    params=params,
                    goal=goal,
                    context={"iteration": iteration, "step": i+1}
                )
                all_judgments.append(judgment)
                
                # 检查是否应该拒绝执行
                if should_refuse(judgment):
                    refusal_msg = generate_refusal_message(judgment)
                    emit("result", refusal_msg)
                    step_errors.append(f"❌ Agent 拒绝执行: {desc}")
                    all_errors.append(f"❌ Agent 拒绝执行: {desc}\n原因: {judgment.reasoning}")
                    agent_refused = True
                    
                    # 记录到错误文件
                    if "history" not in errors_data:
                        errors_data["history"] = []
                    errors_data["history"].append({
                        "step": tool,
                        "error": f"Agent 拒绝执行: {judgment.reasoning}",
                        "iteration": iteration,
                        "judgment_type": judgment.judgment_type.value
                    })
                    safe_write_json(str(ERROR_FILE), errors_data)
                    
                    continue
                
                # 检查是否需要确认
                if needs_confirmation(judgment):
                    emit("confirm", f"⚠️ 此操作需要确认:\n{judgment.to_user_message()}")
                    # 在实际场景中这里应该等待用户确认
                    # 目前自动继续，但记录需要确认
                    emit("status", f"⚠️ 风险等级: {judgment.risk_level.value}")
                
                # 执行步骤（带反思机制）
                exec_result = execute_step_with_reflection(
                    step=step,
                    step_index=i,
                    total_steps=len(steps),
                    context={'iteration': iteration, 'goal': goal},
                    max_retries=3
                )
                
                if exec_result['success']:
                    step_results.append(f"✅ {desc}: {exec_result['result']}")
                    all_results.append(f"✅ {desc}: {exec_result['result']}")
                    emit("result", exec_result['result'])
                    
                    state["completed_steps"].append(desc)
                    safe_write_json(str(STATE_FILE), state)
                    
                    if i < len(plan_data["steps"]):
                        plan_data["steps"][i]["status"] = "done"
                        safe_write_json(str(PLAN_FILE), plan_data)
                else:
                    error_msg = f"步骤失败: {desc} - {exec_result.get('error', '未知错误')}"
                    step_errors.append(error_msg)
                    all_errors.append(error_msg)
                    emit("error", error_msg)
                    
                    if "history" not in errors_data:
                        errors_data["history"] = []
                    errors_data["history"].append({
                        "step": tool, "error": error_msg, "iteration": iteration
                    })
                    safe_write_json(str(ERROR_FILE), errors_data)
            
            # 如果 Agent 拒绝了某些步骤，尝试其他方案
            if agent_refused:
                failed_approaches.append(f"{approach} (Agent 拒绝部分步骤)")
                emit("status", f"🔄 由于安全原因拒绝了部分步骤，尝试其他方案...")
                continue
            
            # 评估结果
            emit("status", "🔍 评估执行结果...")
            evaluation = evaluate_result(goal, step_results, step_errors)
            
            if evaluation["success"]:
                task_result = "\n".join(all_results)
                
                # 生成结论性判断
                if step_errors or all_judgments:
                    emit("status", "📋 生成结论性判断...")
                    try:
                        conclusion = generate_conclusion(
                            problem_description=goal,
                            analysis_data={
                                "results": all_results,
                                "errors": all_errors,
                                "iterations": iteration,
                                "judgments": [j.to_dict() for j in all_judgments]
                            }
                        )
                        task_result += f"\n\n{conclusion.to_report()}"
                    except Exception as e:
                        emit("status", f"⚠️ 生成结论失败: {e}")
                
                memory["history"].append({"user": goal, "assistant": task_result})
                save_memory(memory)
                
                if iteration > 1:
                    save_experience(
                        title=f"任务成功: {goal[:30]}",
                        problem=f"目标: {goal}\n失败方案: {', '.join(failed_approaches)}",
                        solution=f"成功方案: {approach}",
                        lesson=f"经过 {iteration} 次尝试后成功"
                    )
                
                generate_report(user_goal=goal, task_result=task_result)
                emit("done", f"🎉 任务完成！共尝试 {iteration} 次")
                
                state["status"] = "completed"
                safe_write_json(str(STATE_FILE), state)
                clear_context_snapshot(task_id)
                return "DONE"
            
            else:
                failed_approaches.append(approach)
                emit("status", f"❌ 方案 '{approach}' 失败: {evaluation['reason']}")
                emit("status", f"💡 建议: {evaluation['suggestion']}")
                
                if len(failed_approaches) >= MAX_RETRIES:
                    emit("error", f"已尝试 {MAX_RETRIES} 种方案，全部失败")
                    break
                
                emit("status", f"🔄 切换到新方案... (已尝试 {len(failed_approaches)}/{MAX_RETRIES})")
                time.sleep(2)
        
        # 所有尝试都失败
        task_result = f"任务未能完成\n\n尝试的方案:\n" + "\n".join(f"- {a}" for a in failed_approaches)
        if all_results:
            task_result += f"\n\n执行结果:\n" + "\n".join(all_results)
        if all_errors:
            task_result += f"\n\n错误记录:\n" + "\n".join(all_errors)
        
        # 生成失败结论
        try:
            conclusion = generate_conclusion(
                problem_description=f"任务失败: {goal}",
                analysis_data={
                    "results": all_results,
                    "errors": all_errors,
                    "failed_approaches": failed_approaches
                }
            )
            task_result += f"\n\n{conclusion.to_report()}"
        except Exception:
            pass
        
        memory["history"].append({"user": goal, "assistant": task_result})
        save_memory(memory)
        
        save_experience(
            title=f"任务失败: {goal[:30]}",
            problem=f"目标: {goal}",
            solution=f"尝试的方案: {', '.join(failed_approaches)}",
            lesson="所有方案都失败，需要人工介入"
        )
        
        generate_report(user_goal=goal, task_result=task_result)
        emit("done", f"⚠️ 任务未完成，已尝试 {len(failed_approaches)} 种方案")
        
        state["status"] = "failed"
        safe_write_json(str(STATE_FILE), state)
        return "FAILED"

    except Exception as e:
        emit("error", f"{type(e).__name__}: {e}")
        try:
            generate_report(user_goal=goal, task_result=f"任务异常: {e}")
        except Exception:
            pass
        return "FAILED"
    finally:
        release()


def resume_task(task_id: str) -> str:
    """恢复之前中断的任务"""
    context = load_context_snapshot(task_id)
    if not context:
        return "TASK_NOT_FOUND"
    
    goal = context.get("goal", "")
    emit("status", f"🔄 恢复任务: {goal}")
    
    return run_agent(goal)
import re
import json
from typing import Dict, List

def reflect_and_fix(error_message: str, step: dict, context: dict) -> dict:
    """
    分析错误并生成修复方案
    
    Args:
        error_message: 错误信息
        step: 失败的步骤
        context: 执行上下文
    
    Returns:
        {
            'problem_type': 错误类型,
            'root_cause': 根本原因,
            'can_auto_fix': 是否可以自动修复,
            'fix_actions': 修复动作列表,
            'explanation': 修复说明
        }
    """
    
    tool = step.get('tool', '')
    params = step.get('params', {})
    
    if "No module named" in error_message or "模块不存在" in error_message:
        match = re.search(r"No module named '(\w+)'|模块不存在.*?(\w+)", error_message)
        if match:
            module_name = match.group(1) or match.group(2)
            
            emit('thinking', f'🧠 分析: 缺少模块 {module_name}')
            emit('thinking', f'💡 解决方案: 自动创建 {module_name}.py 模块')
            
            module_content = generate_module_skeleton(module_name, {
                'error': error_message,
                'tool': tool,
                'params': params,
                'context': context
            })
            
            return {
                'problem_type': 'module_missing',
                'root_cause': f'缺少模块 {module_name}',
                'can_auto_fix': True,
                'fix_actions': [
                    {
                        'tool': 'write_file',
                        'params': {
                            'path': f'/home/ubuntu/jarvis/{module_name}.py',
                            'content': module_content
                        }
                    }
                ],
                'explanation': f'自动创建 {module_name}.py 模块'
            }
    
    elif "请指定" in error_message or "未指定" in error_message or "缺少" in error_message:
        emit('thinking', f'🧠 分析: 工具调用缺少必要参数')
        emit('thinking', f'💡 解决方案: 重新生成包含完整参数的步骤')
        
        return {
            'problem_type': 'param_missing',
            'root_cause': '工具调用缺少必要参数',
            'can_auto_fix': False,
            'fix_actions': [],
            'explanation': '需要重新规划步骤，补充完整参数'
        }
    
    elif "测试失败" in error_message or "导入失败" in error_message:
        emit('thinking', f'🧠 分析: 代码逻辑或依赖问题')
        
        return {
            'problem_type': 'logic_error',
            'root_cause': '代码逻辑或依赖问题',
            'can_auto_fix': False,
            'fix_actions': [],
            'explanation': '需要深度分析代码逻辑'
        }
    
    else:
        emit('thinking', f'🧠 分析: 未知错误类型，需要人工介入')
        
        return {
            'problem_type': 'unknown',
            'root_cause': error_message,
            'can_auto_fix': False,
            'fix_actions': [],
            'explanation': '未知错误类型'
        }


def generate_module_skeleton(module_name: str, context: dict) -> str:
    """
    根据上下文生成模块骨架
    """
    
    prompt = f"""你需要创建一个Python模块 {module_name}.py

上下文信息：
- 错误：{context.get('error', '')}
- 调用工具：{context.get('tool', '')}
- 工具参数：{json.dumps(context.get('params', {}), ensure_ascii=False)}

要求：
1. 分析错误信息，理解需要什么类或函数
2. 生成基本的类和函数定义
3. 不写注释
4. 保持代码简洁
5. 确保可以被正常导入

直接输出Python代码，不要markdown格式。
"""
    
    try:
        code = call_llm(prompt)
        if '```python' in code:
            code = code.split('```python')[1].split('```')[0].strip()
        elif '```' in code:
            code = code.split('```')[1].split('```')[0].strip()
        
        return code
    except Exception as e:
        emit('error', f'生成模块骨架失败: {e}')
        return f"""
class {module_name.capitalize()}:
    pass

def main():
    pass
"""


def execute_fix(fix_actions: List[dict]) -> dict:
    """
    执行修复动作
    """
    emit('status', '🔧 开始执行自动修复...')
    
    for i, action in enumerate(fix_actions):
        emit('tool_call', f"修复动作 {i+1}/{len(fix_actions)}: {action['tool']}")
        
        try:
            command = f"RUN{json.dumps(action)}"
            result = execute(command)
            
            if "错误" in str(result) or "失败" in str(result):
                emit('error', f"❌ 修复动作失败: {result}")
                return {'success': False, 'error': result}
            
            emit('tool_result', f"✅ {result}")
            
        except Exception as e:
            emit('error', f"❌ 修复执行异常: {e}")
            return {'success': False, 'error': str(e)}
    
    emit('status', '✅ 自动修复完成')
    return {'success': True}


def execute_step_with_reflection(step: dict, step_index: int, total_steps: int, context: dict, max_retries: int = 3) -> dict:
    """
    执行步骤，失败时自动反思并修复
    
    Args:
        step: 步骤定义
        step_index: 步骤索引
        total_steps: 总步骤数
        context: 执行上下文
        max_retries: 最大重试次数
    
    Returns:
        {'success': bool, 'result': str, 'error': str}
    """
    
    tool = step.get('tool', '')
    params = step.get('params', {})
    desc = step.get('description', f'执行 {tool}')
    
    emit('status', f"步骤 {step_index + 1}/{total_steps}: {desc}")
    
    for attempt in range(max_retries):
        try:
            emit('tool_call', f"🔧 调用工具: {tool} | 参数: {json.dumps(params, ensure_ascii=False)[:100]}...")
            
            command = f"RUN{json.dumps({'tool': tool, 'params': params})}"
            result = execute(command)
            
            result_str = str(result)
            
            if "错误" in result_str or "失败" in result_str or "❌" in result_str:
                emit('error', f"⚠️ 步骤执行失败: {result_str[:200]}")
                
                reflection = reflect_and_fix(result_str, step, context)
                emit('thinking', f"🧠 反思结果: {reflection['explanation']}")
                
                if reflection['can_auto_fix'] and attempt < max_retries - 1:
                    emit('status', '🔧 尝试自动修复...')
                    fix_result = execute_fix(reflection['fix_actions'])
                    
                    if fix_result['success']:
                        emit('status', '✅ 修复成功，重试步骤...')
                        continue
                    else:
                        emit('error', '❌ 自动修复失败')
                        if attempt < max_retries - 1:
                            emit('status', f'🔄 重试 {attempt + 2}/{max_retries}...')
                            continue
                else:
                    if not reflection['can_auto_fix']:
                        emit('status', '⚠️ 无法自动修复，需要重新规划')
                    
                    if attempt < max_retries - 1:
                        emit('status', f'🔄 重试 {attempt + 2}/{max_retries}...')
                        continue
                    else:
                        return {'success': False, 'error': result_str, 'result': result_str}
            else:
                emit('tool_result', f"✅ {result_str[:200]}..." if len(result_str) > 200 else f"✅ {result_str}")
                return {'success': True, 'result': result_str}
                
        except Exception as e:
            emit('error', f"❌ 执行异常: {e}")
            
            if attempt < max_retries - 1:
                emit('status', f"🔄 重试 {attempt + 2}/{max_retries}...")
            else:
                return {'success': False, 'error': str(e), 'result': str(e)}
    
    return {'success': False, 'error': '达到最大重试次数', 'result': '达到最大重试次数'}
