import json
import re
from agent import create_dynamic_plan, run_agent
from llm import think, chat

def test_plan_parsing():
    print("--- 测试计划解析 ---")
    goal = "贾维斯，请确认你现在是否正在使用本地的 DeepSeek-R1 模型？"
    memory = {"history": [], "context": {}}
    
    print(f"目标: {goal}")
    try:
        plan = create_dynamic_plan(goal, memory)
        print(f"解析出的计划: {json.dumps(plan, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"解析失败: {e}")

def test_full_run():
    print("\n--- 测试完整运行流程 ---")
    goal = "你好"
    try:
        result = run_agent(goal)
        print(f"最终结果: {result}")
    except Exception as e:
        print(f"运行失败: {e}")

if __name__ == "__main__":
    test_plan_parsing()
    test_full_run()
