#!/usr/bin/env python3
"""
测试贾维斯的双API配置
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from llm import call_llm, load_secrets

def test_deepseek_api():
    """测试 DeepSeek 官方 API"""
    print("\n" + "="*60)
    print("测试 1: DeepSeek 官方 API")
    print("="*60)
    
    secrets = load_secrets()
    print(f"DeepSeek API Key: {secrets.get('deepseek_api_key', 'NOT FOUND')[:20]}...")
    print(f"DeepSeek Base URL: {secrets.get('deepseek_base_url', 'NOT FOUND')}")
    
    try:
        response = call_llm(
            system_prompt="你是一个测试助手，请简短回复。",
            user_prompt="请用一句话介绍你自己。"
        )
        print(f"\n✅ DeepSeek API 调用成功！")
        print(f"响应: {response[:200]}...")
        return True
    except Exception as e:
        print(f"\n❌ DeepSeek API 调用失败: {e}")
        return False


def test_openai_api():
    """测试老张令牌（OpenAI 兼容 API）"""
    print("\n" + "="*60)
    print("测试 2: 老张令牌（OpenAI 兼容 API）")
    print("="*60)
    
    secrets = load_secrets()
    print(f"OpenAI API Key: {secrets.get('openai_api_key', 'NOT FOUND')[:20]}...")
    print(f"OpenAI Base URL: {secrets.get('openai_base_url', 'NOT FOUND')}")
    
    # 临时修改配置，只使用 OpenAI API
    import json
    secrets_file = Path(__file__).parent / "secrets.json"
    original_secrets = secrets.copy()
    
    try:
        # 临时禁用 DeepSeek，只测试 OpenAI
        test_secrets = original_secrets.copy()
        test_secrets["enable_deepseek"] = False
        test_secrets["enable_openai"] = True
        
        with open(secrets_file, "w", encoding="utf-8") as f:
            json.dump(test_secrets, f, ensure_ascii=False, indent=4)
        
        response = call_llm(
            system_prompt="你是一个测试助手，请简短回复。",
            user_prompt="请用一句话介绍你自己。"
        )
        print(f"\n✅ OpenAI API 调用成功！")
        print(f"响应: {response[:200]}...")
        return True
    except Exception as e:
        print(f"\n❌ OpenAI API 调用失败: {e}")
        return False
    finally:
        # 恢复原始配置
        with open(secrets_file, "w", encoding="utf-8") as f:
            json.dump(original_secrets, f, ensure_ascii=False, indent=4)


def test_failover():
    """测试失败重试机制"""
    print("\n" + "="*60)
    print("测试 3: 失败重试机制")
    print("="*60)
    
    secrets = load_secrets()
    print(f"Primary Provider: {secrets.get('primary_provider', 'deepseek')}")
    print(f"Enable DeepSeek: {secrets.get('enable_deepseek', True)}")
    print(f"Enable OpenAI: {secrets.get('enable_openai', True)}")
    
    try:
        response = call_llm(
            system_prompt="你是一个测试助手，请简短回复。",
            user_prompt="请说'测试成功'。"
        )
        print(f"\n✅ 失败重试机制正常！")
        print(f"响应: {response}")
        return True
    except Exception as e:
        print(f"\n❌ 失败重试机制异常: {e}")
        return False


if __name__ == "__main__":
    print("\n🧪 开始测试贾维斯的双API配置...")
    
    results = {
        "DeepSeek API": test_deepseek_api(),
        "OpenAI API": test_openai_api(),
        "失败重试": test_failover()
    }
    
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 所有测试通过！贾维斯的双API配置正常工作。")
    else:
        print("\n⚠️ 部分测试失败，请检查配置。")
    
    sys.exit(0 if all_passed else 1)
