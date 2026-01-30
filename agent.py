"""
JARVIS 智能代理模块 (v1.9.0) - 工业级演化版
核心特性：
- Parallel Evolution (并行演化)：多分支方案并行测试
- Visual Semantic Memory (视觉语义记忆)：UI 状态指纹识别
- Dynamic Resource Orchestration (动态资源调度)：算力自动分流
- 工具元认知 (Tool Meta-Cognition)：深度理解工具的适用场景与风险
- 深度自省 (Deep Reflection)：失败后自动分析原因
"""
import json
import threading
import re
import time
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any

# 导入跨平台工具
from platform_compatibility import normalize_path, is_windows
from llm import think, chat
from executor import execute, get_available_tools_with_meta

# 工具参数验证规则 (v1.7.4)
TOOL_PARAM_RULES = {
    "write_file": {"required": ["path", "content"]},
    "read_file": {"required": ["path"]},
    "run_shell": {"required": ["command"]},
    "scan_files": {"required": []},
    "create_new_tool": {"required": ["name", "code"]},
}

def validate_tool_params(tool, params):
    """验证工具参数是否完整"""
    if tool not in TOOL_PARAM_RULES:
        return True, None  # 未知工具，不验证
    
    rules = TOOL_PARAM_RULES[tool]
    params = params or {}
    
    # 检查必需参数
    missing = [p for p in rules["required"] if not params.get(p)]
    if missing:
        return False, f"参数验证失败: {tool} 缺少必需参数 {', '.join(missing)}"
    
    return True, None
from run_lock import acquire, release
from safe_io import safe_write_json, safe_read_json
from event_bus import emit

# v1.9.0 新增模块导入

# v2.0.0 强自主AI架构（可选）
USE_V2_ARCHITECTURE = False  # 设置为True启用新架构

try:
    from capability_box import CapabilityBox
    from autonomous_goal_generator import AutonomousGoalGenerator
    from resilient_executor import ResilientExecutor
    from intent_inference import IntentInferenceEngine
    from meta_cognition import MetaCognition
    from memory_system import MemorySystem
    V2_AVAILABLE = True
except ImportError:
    V2_AVAILABLE = False
try:
    from parallel_evolution import ParallelEvolution
    from visual_memory import VisualMemory
    from resource_orchestrator import ResourceOrchestrator
except ImportError:
    # 容错处理：如果模块尚未完全实现，使用 Mock 类
    class ParallelEvolution: pass
    class VisualMemory: pass
    class ResourceOrchestrator: pass

# 文件路径归一化
_ROOT = Path(__file__).parent.absolute()
STATE_FILE = normalize_path(_ROOT / "STATE.json")
PLAN_FILE = normalize_path(_ROOT / "PLAN.json")
MEMORY_FILE = normalize_path(_ROOT / "CHAT_MEMORY.json")

# 配置
MAX_ITERATIONS = 50

class JarvisAgent:
    def __init__(self):
        self.version = "1.9.0"
        self.orchestrator = ResourceOrchestrator()
        self.visual_mem = VisualMemory()
        self.evolver = ParallelEvolution()

    def load_memory(self) -> dict:
        default = {"history": [], "context": {}}
        return safe_read_json(MEMORY_FILE, default=default)

    def reflect_on_failures(self, failed_steps: List[Dict]) -> str:
        """深度自省：分析失败原因"""
        if not failed_steps: return ""
        prompt = f"分析以下失败步骤并给出改进建议：\n{json.dumps(failed_steps, ensure_ascii=False, indent=2)}"
        try: return think(prompt)
        except: return "自省失败，尝试更换方案。"

    def create_dynamic_plan(self, goal: str, memory: dict, reflection: str = "") -> dict:
        """根据用户目标、工具元数据和自省结论制定计划"""
        tools_with_meta = get_available_tools_with_meta()
        tools_desc = json.dumps(tools_with_meta, ensure_ascii=False, indent=2)
        
        platform_info = "Windows 11" if is_windows() else "Linux (Ubuntu)"
        reflection_context = f"\n## 深度自省结论\n{reflection}\n" if reflection else ""
        
        # v1.9.0 动态资源调度：根据目标复杂度选择模型
        # complexity = self.orchestrator.analyze_complexity(goal)
        
        prompt = f"""你是一个对标 Manus 的智能代理，正在 {platform_info} 环境下运行。
请分析用户目标并制定执行计划。

## 工具元认知 (你的武器库)
你可以深度理解以下工具的用途、风险和平台特性：
{tools_desc}

{reflection_context}

## 核心原则 (v1.9.0)
1. **并行演化**：对于高风险操作，考虑使用 `parallel_evolution` 进行多方案测试。
2. **视觉记忆**：UI 操作后使用 `visual_memory` 校验状态指纹。
3. **工具匹配**：根据工具的 meta 信息选择最合适的工具。
4. **视觉验证**：必须包含截图步骤进行视觉验证。

## 用户目标
{goal}

## 重要：JSON 格式要求
必须返回严格的 JSON 格式，不要添加任何额外文本。

必须包含所有必需参数：
- write_file: 必须有 path 和 content
- read_file: 必须有 path
- run_shell: 必须有 command
- scan_files: 可选 path

JSON 示例：
{{
    "understanding": "简洁描述目标理解",
    "approach": "方案名称",
    "steps": [
        {{"tool": "scan_files", "params": {{"path": "."}}, "description": "扫描项目文件"}},
        {{"tool": "write_file", "params": {{"path": "demo.py", "content": "print('test')"}}, "description": "创建演示文件"}}
    ]
}}
"""
        try:
            response = think(prompt)
            
            # 策略1: 提取最外层的JSON对象
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                json_str = json_match.group()
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    print(f"[PLAN] JSON解析失败: {e}")
                    
                    # 策略2: 尝试修复JSON（移除尾部多余字符）
                    try:
                        # 找到最后一个完整的}
                        last_brace = json_str.rfind('}')
                        if last_brace > 0:
                            fixed_json = json_str[:last_brace+1]
                            return json.loads(fixed_json)
                    except:
                        pass
                    
                    # 策略3: 记录原始响应以便调试
                    print(f"[PLAN] 原始响应: {response[:500]}...")
        except Exception as e: 
            print(f"[PLAN] 失败: {e}")
        
        return {"understanding": goal, "approach": "默认方案", "steps": []}

    def run(self, goal: str) -> str:
        """运行智能代理 - v1.9.0"""
        acquire()
        task_id = str(uuid.uuid4())[:8]
        iteration = 0
        failed_steps = []
        reflection = ""
        
        try:
            emit("status", "贾维斯 v2")
            memory = self.load_memory()
            
            while iteration < MAX_ITERATIONS:
                iteration += 1
                emit("status", f"📋 正在进行第 {iteration} 次尝试...")
                
                plan = self.create_dynamic_plan(goal, memory, reflection)
                steps = plan.get("steps", [])
                
                if not steps:
                    response = chat(goal)
                    emit("assistant", response)
                    return response
                
                success_count = 0
                for step in steps:
                    tool = step.get("tool")
                    params = step.get("params", {})
                    desc = step.get("description", "")
                    
                    # 参数验证 (v1.7.4)
                    valid, error_msg = validate_tool_params(tool, params)
                    if not valid:
                        emit("status", f"⚠️ {error_msg}")
                        failed_steps.append({"step": step, "error": error_msg})
                        reflection = self.reflect_on_failures(failed_steps[-3:])
                        break
                    
                    emit("thinking", f"🛠️ 执行: {desc}")
                    result = execute(f"RUN {json.dumps({'tool': tool, 'params': params})}")
                    
                    # 只检查特定的错误格式开头，避免误判正常内容中包含"错误"字符的情况
                    result_str = str(result)
                    if result_str.startswith(('错误：', '执行失败', '执行异常', '读取失败', '写入失败', '未知工具', '参数验证失败')):
                        emit("status", f"⚠️ 步骤失败: {tool}")
                        failed_steps.append({"step": step, "error": result})
                        reflection = self.reflect_on_failures(failed_steps[-3:])
                        break
                    else:
                        success_count += 1
                        emit("status", f"✅ 完成: {tool}")
                        if tool == "self_modify_restart": return "🔄 正在重启..."
                
                if success_count == len(steps): break
                    
            final_msg = f"任务执行完成。共迭代 {iteration} 次。"
            emit("assistant", final_msg)
            return final_msg
        except Exception as e:
            error_msg = f"❌ 异常: {str(e)}"
            emit("error", error_msg)
            return error_msg
        finally:
            release()

def run_agent(goal: str):
    """JARVIS Agent 入口函数，支持v1.9和v2.0架构"""
    if USE_V2_ARCHITECTURE and V2_AVAILABLE:
        # 使用v2.0强自主AI架构
        from agent_v2 import JarvisAgentV2
        agent_v2 = JarvisAgentV2()
        return agent_v2.run(goal)
    else:
        # 使用v1.9传统架构
        agent = JarvisAgent()
        return agent.run(goal)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1: run_agent(sys.argv[1])
