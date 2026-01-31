from agent import run_agent
import time

questions = [
    "你好，贾维斯！",
    "请介绍一下你的核心能力，特别是关于技能进化的部分。",
    "帮我创建一个名为 hello_jarvis.txt 的文件，内容写上 'Local R1 is Awesome!'",
    "确认一下刚才的文件是否创建成功，并告诉我你现在的状态。"
]

for i, q in enumerate(questions):
    print(f"\n\n{'='*20} 对话 {i+1} {'='*20}")
    print(f"👤 用户: {q}")
    print("🤖 贾维斯正在思考...")
    start_time = time.time()
    response = run_agent(q)
    end_time = time.time()
    print(f"\n✨ 最终回复 ({end_time - start_time:.2f}s):")
    print(response)
    time.sleep(1)
