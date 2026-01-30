"""测试代码分析器"""
import sys
sys.path.append('/home/ubuntu/jarvis')

from code_analyzer import CodeAnalyzer

print("=== 测试代码分析器 ===\n")

analyzer = CodeAnalyzer("/home/ubuntu/jarvis")

# 测试1: 获取项目结构
print("1. 获取项目结构...")
structure = analyzer._get_project_structure()
print(f"   总文件数: {structure['total_files']}")
print(f"   总行数: {structure['total_lines']}")
print(f"   前5个模块: {[m['name'] for m in structure['modules'][:5]]}")

# 测试2: 读取关键文件
print("\n2. 读取关键文件...")
key_files = analyzer._read_key_files()
print(f"   读取了 {len(key_files)} 个关键文件")
print(f"   文件列表: {list(key_files.keys())}")

# 测试3: 简单的LLM调用测试
print("\n3. 测试LLM调用...")
try:
    from llm import chat
    response = chat("请用一句话总结JARVIS项目的目标")
    print(f"   LLM响应: {response[:100]}...")
except Exception as e:
    print(f"   LLM调用失败: {e}")

print("\n✅ 基础功能测试完成！")
