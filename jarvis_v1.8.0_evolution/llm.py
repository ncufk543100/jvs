"""
JARVIS LLM 模块
支持 DeepSeek API、OpenAI 兼容 API 和本地 Ollama 模型
"""
import json
import subprocess
import re
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
            temperature=0.3
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        print(f"[API] {provider} call failed:", e)
        raise


def call_local_model(prompt):
    """调用本地 Ollama 模型"""
    try:
        # 优先尝试通过 OpenAI 兼容接口调用 Ollama (更稳定)
        client = OpenAI(api_key="ollama", base_url="http://127.0.0.1:11434/v1", timeout=120)
        r = client.chat.completions.create(
            model="deepseek-r1:14b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return r.choices[0].message.content
    except Exception as e:
        # 备选：直接调用命令行
        try:
            p = subprocess.run(
                ["ollama", "run", "deepseek-r1:14b"],
                input=prompt.encode(),
                capture_output=True,
                timeout=120
            )
            return p.stdout.decode(errors="ignore")
        except:
            return f"本地模型调用失败: {e}"


def call_llm(system_prompt: str, user_prompt: str) -> str:
    """
    统一的 LLM 调用接口，支持多个 API 提供商
    """
    # 优先尝试本地 Ollama R1:14b
    try:
        print("[MODEL] trying local ollama (deepseek-r1:14b)")
        result = call_local_model(system_prompt + "\n" + user_prompt)
        if not result.startswith("本地模型调用失败"):
            print("[MODEL] local ollama succeeded")
            # 过滤 R1 的思考过程标签 <think>...</think>
            clean_result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL).strip()
            return clean_result
        print("[MODEL] local ollama not available")
    except Exception as e:
        print(f"[MODEL] local ollama failed: {e}")
    
    # 降级到云端 API
    secrets = load_secrets()
    primary = secrets.get("primary_provider", "deepseek")
    enable_ds = secrets.get("enable_deepseek", True)
    enable_openai = secrets.get("enable_openai", True)
    
    ds_key = secrets.get("deepseek_api_key", "").strip()
    ds_url = secrets.get("deepseek_base_url", "https://api.deepseek.com")
    
    openai_key = secrets.get("openai_api_key", "").strip()
    openai_url = secrets.get("openai_base_url", "https://api.laozhang.ai/v1")
    
    providers = []
    if primary == "deepseek" and enable_ds and ds_key:
        providers.append(("deepseek", "deepseek-chat", ds_key, ds_url))
    if enable_openai and openai_key:
        providers.append(("openai", "gpt-4o", openai_key, openai_url))
    if primary != "deepseek" and enable_ds and ds_key:
        providers.append(("deepseek", "deepseek-chat", ds_key, ds_url))
    
    for provider_name, model, api_key, base_url in providers:
        try:
            print(f"[MODEL] trying {provider_name} ({model})")
            result = call_api(provider_name, model, system_prompt, user_prompt, api_key, base_url)
            print(f"[MODEL] {provider_name} succeeded")
            return result
        except Exception as e:
            print(f"[MODEL] {provider_name} failed: {e}")
            continue
    
    raise Exception("所有 LLM 提供商都不可用")


def think(prompt: str, memory: str = "") -> str:
    system_prompt = """你是【必须完成任务的工程执行体】。
失败必须换方案继续，直到 DONE。
请用 JSON 格式回复任务计划。
"""
    if memory:
        user_prompt = f"目标：\n{prompt}\n\n历史：\n{memory}\n"
    else:
        user_prompt = prompt
    
    return call_llm(system_prompt, user_prompt)


def chat(prompt: str) -> str:
    system_prompt = """你是 JARVIS，一个智能工程助手。请用简洁友好的中文回复用户。"""
    return call_llm(system_prompt, prompt)
