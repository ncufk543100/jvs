"""
ClawedBot LLM 模块
支持 DeepSeek API 和本地 Ollama 模型
"""
import json
import subprocess
from pathlib import Path
from openai import OpenAI

BASE_URL = "https://api.deepseek.com"
ROOT = Path(__file__).parent
SECRETS_FILE = ROOT / "secrets.json"


def load_secrets():
    if not SECRETS_FILE.exists():
        print("[CONFIG] secrets.json not found")
        return {}
    try:
        return json.loads(SECRETS_FILE.read_text(encoding="utf-8-sig"))
    except Exception as e:
        print("[CONFIG] secrets.json invalid:", e)
        return {}


def call_deepseek(model, system_prompt, user_prompt, api_key):
    """调用 DeepSeek API"""
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.gptsapi.net/v1"
    )
    r = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3
    )
    return r.choices[0].message.content.strip()


def call_local_model(prompt):
    """调用本地 Ollama 模型"""
    try:
        p = subprocess.run(
            ["ollama", "run", "deepseek-r1:14b"],
            input=prompt.encode(),
            capture_output=True,
            timeout=60
        )
        return p.stdout.decode(errors="ignore")
    except Exception as e:
        return f"本地模型调用失败: {e}"


def think(prompt: str, memory: str = "") -> str:
    """
    思考并规划任务
    
    Args:
        prompt: 用户目标或完整的 prompt
        memory: 可选的历史记忆上下文
    
    Returns:
        LLM 的响应
    """
    secrets = load_secrets()
    api_key = secrets.get("deepseek_api_key", "").strip()
    enable_ds = secrets.get("enable_deepseek", True)

    system_prompt = """你是【必须完成任务的工程执行体】。
失败必须换方案继续，直到 DONE。
请用 JSON 格式回复任务计划。
"""
    
    # 构建用户 prompt
    if memory:
        user_prompt = f"""目标：
{prompt}

历史：
{memory}
"""
    else:
        user_prompt = prompt

    if enable_ds and api_key:
        try:
            print("[MODEL] using deepseek-chat")
            return call_deepseek("gpt-4.1-mini", system_prompt, user_prompt, api_key)
        except Exception as e:
            print("[MODEL] deepseek-chat failed:", e)

        try:
            print("[MODEL] using deepseek-reasoner")
            return call_deepseek("gpt-4.1-mini", system_prompt, user_prompt, api_key)
        except Exception as e:
            print("[MODEL] deepseek-reasoner failed:", e)

    print("[MODEL] fallback to local model")
    return call_local_model(system_prompt + "\n" + user_prompt)


def chat(prompt: str) -> str:
    """通用对话接口"""
    secrets = load_secrets()
    api_key = secrets.get("deepseek_api_key", "").strip()
    enable_ds = secrets.get("enable_deepseek", True)

    system_prompt = """你是 ClawedBot，一个智能工程助手。你可以帮助用户:
- 扫描和分析项目文件
- 读取和写入文件
- 执行 Shell 命令
- 分析代码结构
- 查看 Git 状态和历史
- 搜索文件内容

请用简洁友好的中文回复用户。如果需要执行操作，请明确说明你将使用什么工具。
"""

    if enable_ds and api_key:
        try:
            print("[CHAT] using deepseek-chat")
            return call_deepseek("gpt-4.1-mini", system_prompt, prompt, api_key)
        except Exception as e:
            print("[CHAT] deepseek-chat failed:", e)
    
    print("[CHAT] fallback to local model")
    return call_local_model(system_prompt + "\n" + prompt)


def plan_tasks(goal: str, available_tools: dict) -> str:
    """规划任务执行步骤"""
    secrets = load_secrets()
    api_key = secrets.get("deepseek_api_key", "").strip()
    enable_ds = secrets.get("enable_deepseek", True)

    tools_desc = "\n".join([f"- {name}: {desc}" for name, desc in available_tools.items()])
    
    system_prompt = f"""你是一个任务规划专家。根据用户目标，选择合适的工具创建执行计划。

可用工具:
{tools_desc}

返回 JSON 格式的计划:
{{
    "understanding": "对用户需求的理解",
    "steps": [
        {{"tool": "工具名", "params": {{}}, "description": "步骤说明"}}
    ]
}}

只返回 JSON，不要其他内容。
"""

    if enable_ds and api_key:
        try:
            return call_deepseek("gpt-4.1-mini", system_prompt, goal, api_key)
        except Exception as e:
            print("[PLAN] deepseek failed:", e)
    
    return call_local_model(system_prompt + "\n" + goal)


def analyze_code(code: str, focus: str = "general") -> str:
    """
    分析代码质量
    
    Args:
        code: 要分析的代码
        focus: 分析焦点 (general, bugs, performance, security)
    
    Returns:
        分析结果
    """
    secrets = load_secrets()
    api_key = secrets.get("deepseek_api_key", "").strip()
    enable_ds = secrets.get("enable_deepseek", True)

    focus_prompts = {
        "general": "请全面分析这段代码的质量，包括代码风格、可读性、潜在问题等。",
        "bugs": "请重点分析这段代码中可能存在的 bug 和逻辑错误。",
        "performance": "请分析这段代码的性能问题和优化建议。",
        "security": "请分析这段代码的安全隐患。"
    }
    
    system_prompt = f"""你是一个资深代码审查专家。
{focus_prompts.get(focus, focus_prompts['general'])}

请用以下格式回复：
## 问题发现
- 问题1: 描述
- 问题2: 描述

## 改进建议
- 建议1: 描述
- 建议2: 描述

## 代码评分
- 可读性: X/10
- 健壮性: X/10
- 性能: X/10
"""

    if enable_ds and api_key:
        try:
            return call_deepseek("gpt-4.1-mini", system_prompt, code, api_key)
        except Exception as e:
            print("[ANALYZE] deepseek failed:", e)
    
    return call_local_model(system_prompt + "\n" + code)
