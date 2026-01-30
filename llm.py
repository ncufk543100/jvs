"""
JARVIS LLM 模块
支持 DeepSeek API、OpenAI 兼容 API 和本地 Ollama 模型
"""
import json
import subprocess
from pathlib import Path
from openai import OpenAI

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


def call_api(provider, model, system_prompt, user_prompt, api_key, base_url):
    """调用 API（DeepSeek 或 OpenAI 兼容）"""
    try:
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        r = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            timeout=60
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        print(f"[API] {provider} call failed:", e)
        raise


def call_local_model(prompt):
    """调用本地 Ollama 模型，优先使用 HTTP API (v2.0.1)"""
    OLLAMA_MODEL = "deepseek-r1:14b"
    OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"
    
    # 策略1: 优先使用 Ollama HTTP API（更稳定，跨平台兼容性好）
    try:
        import requests
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "")
        else:
            print(f"[OLLAMA HTTP] 状态码 {response.status_code}")
    except ImportError:
        print("[OLLAMA HTTP] requests 库未安装，尝试命令行方式")
    except Exception as e:
        print(f"[OLLAMA HTTP] HTTP API 调用失败: {e}")
    
    # 策略2: 降级到命令行方式
    try:
        # 检查 ollama 命令是否可用
        subprocess.run(["ollama", "--version"], check=True, capture_output=True, timeout=5)
        
        # 运行模型
        p = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL],
            input=prompt.encode(),
            capture_output=True,
            timeout=60
        )
        return p.stdout.decode(errors="ignore")
    except FileNotFoundError:
        return "本地模型调用失败: Ollama 未安装或未配置到 PATH。"
    except Exception as e:
        return f"本地模型调用失败: {e}"


def call_llm(system_prompt: str, user_prompt: str) -> str:
    """
    统一的 LLM 调用接口，支持多个 API 提供商
    
    调用顺序：
    1. 本地 Ollama R1:14b（优先）
    2. DeepSeek API（降级）
    3. OpenAI 兼容 API（最后备用）
    """
    # 优先尝试本地 Ollama R1:14b
    try:
        print("[MODEL] trying local ollama (deepseek-r1:14b)")
        result = call_local_model(system_prompt + "\n" + user_prompt)
        if not result.startswith("本地模型调用失败"):
            print("[MODEL] local ollama succeeded")
            return result
        print("[MODEL] local ollama not available")
    except Exception as e:
        print(f"[MODEL] local ollama failed: {e}")
    
    # 降级到云端 API
    secrets = load_secrets()
    
    # 读取配置
    primary = secrets.get("primary_provider", "deepseek")
    enable_ds = secrets.get("enable_deepseek", True)
    enable_openai = secrets.get("enable_openai", True)
    
    ds_key = secrets.get("deepseek_api_key", "").strip()
    ds_url = secrets.get("deepseek_base_url", "https://api.deepseek.com")
    
    openai_key = secrets.get("openai_api_key", "").strip()
    openai_url = secrets.get("openai_base_url", "https://api.laozhang.ai/v1")
    
    # 定义提供商列表
    providers = []
    
    if primary == "deepseek" and enable_ds and ds_key:
        providers.append(("deepseek", "deepseek-chat", ds_key, ds_url))
    if enable_openai and openai_key:
        providers.append(("openai", "gpt-5.2", openai_key, openai_url))
    if primary != "deepseek" and enable_ds and ds_key:
        providers.append(("deepseek", "deepseek-chat", ds_key, ds_url))
    
    # 依次尝试每个提供商
    for provider_name, model, api_key, base_url in providers:
        try:
            print(f"[MODEL] trying {provider_name} ({model})")
            result = call_api(provider_name, model, system_prompt, user_prompt, api_key, base_url)
            print(f"[MODEL] {provider_name} succeeded")
            return result
        except Exception as e:
            print(f"[MODEL] {provider_name} failed: {e}")
            continue
    
    # 所有都失败
    raise Exception("所有 LLM 提供商都不可用")


def think(prompt: str, memory: str = "") -> str:
    """
    思考并规划任务
    
    Args:
        prompt: 用户目标或完整的 prompt
        memory: 可选的历史记忆上下文
    
    Returns:
        LLM 的响应
    """
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
    
    return call_llm(system_prompt, user_prompt)


def chat(prompt: str) -> str:
    """通用对话接口"""
    system_prompt = """你是 JARVIS，一个智能工程助手。你可以帮助用户:
- 扫描和分析项目文件
- 读取和写入文件
- 执行 Shell 命令
- 分析代码结构
- 查看 Git 状态和历史
- 搜索文件内容

请用简洁友好的中文回复用户。如果需要执行操作，请明确说明你将使用什么工具。
"""
    
    return call_llm(system_prompt, prompt)


def plan_tasks(goal: str, available_tools: dict) -> str:
    """规划任务执行步骤"""
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
    
    return call_llm(system_prompt, goal)


def analyze_code(code: str, focus: str = "general") -> str:
    """
    分析代码质量
    
    Args:
        code: 要分析的代码
        focus: 分析焦点 (general, bugs, performance, security)
    
    Returns:
        分析结果
    """
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
    
    return call_llm(system_prompt, code)
