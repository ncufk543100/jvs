# JARVIS 卡住问题分析与解决方案

**问题**: JARVIS 在执行任务时产生 3 个事件后卡住，120 秒超时终止

---

## 根本原因

### 1. LLM API 调用没有超时保护

**位置**: `llm.py` 第 32 行

```python
r = client.chat.completions.create(
    model=model,
    messages=[...],
    temperature=0.3
)  # 没有 timeout 参数！
```

**影响**:
- 当 DeepSeek API 响应慢或挂起时，JARVIS 会无限等待
- 用户无法感知进度
- 最终被外部 timeout 强制终止

**解决方案**:
```python
r = client.chat.completions.create(
    model=model,
    messages=[...],
    temperature=0.3,
    timeout=60  # 添加 60 秒超时
)
```

### 2. 工具执行失败判断逻辑过于简单

**位置**: `agent.py` 第 142 行

```python
if "错误" in str(result) or "❌" in str(result):
    # 判定为失败
```

**问题**:
- 如果工具返回的**正常内容**中包含"错误"或"❌"字符，会被误判为失败
- 例如：读取包含错误日志的文件
- 导致无意义的重试循环

**但是**：这个逻辑的**本意是好的** —— 让 JARVIS 能够识别失败并自我反思、试错。

**更好的解决方案**:

#### 方案A：改进字符串判断（短期）
```python
# 检查特定的错误格式
if (str(result).startswith('错误：') or 
    str(result).startswith('执行失败') or 
    str(result).startswith('执行异常')):
    # 判定为失败
```

#### 方案B：结构化返回值（长期，推荐）
```python
# 工具返回结构化数据
{
    "success": True/False,
    "data": "...",
    "error": "..."
}

# Agent 判断
if not result.get("success"):
    # 判定为失败
```

---

## 为什么 JARVIS 自己修复时也卡住？

**讽刺的循环**:
1. JARVIS 尝试读取 `agent.py` 来修复 bug
2. `agent.py` 文件内容包含 "错误" 和 "❌" 字符
3. 被自己的 bug 误判为失败
4. 无法完成修复

**这是一个自我阻塞的死循环！**

---

## 推荐的修复顺序

### 第一步：添加 LLM API 超时（紧急）

**任务**: 修改 `llm.py` 的 `call_api` 函数

```python
# 在 OpenAI client.chat.completions.create() 调用中添加
timeout=60
```

**重要性**: ⭐⭐⭐⭐⭐
- 这是导致卡住的直接原因
- 修复后 JARVIS 不会再无限等待

### 第二步：优化工具失败判断（重要）

**方案1**: 短期改进（立即可做）
- 改为检查特定错误格式（以"错误："开头）
- 避免误判正常内容

**方案2**: 长期重构（需要时间）
- 所有工具返回结构化数据
- Agent 根据 `success` 字段判断
- 保留试错能力的同时提高准确性

### 第三步：优化本地 Ollama 调用（可选）

**当前状态**: 使用命令行 `ollama run`
**优化方向**: 使用 HTTP API (http://localhost:11434/api/generate)

**优点**:
- 更快的响应速度
- 更好的跨平台兼容性
- 可以设置 timeout

---

## 给 JARVIS 的修复指令

### 任务 1: 添加 LLM API 超时

```
修复任务：在 llm.py 的 call_api 函数中，给 client.chat.completions.create() 
调用添加 timeout=60 参数。这样当 API 响应超过 60 秒时会抛出异常，
避免无限等待。修改后提交到 GitHub 并更新版本号到 1.7.3。
```

### 任务 2: 优化失败判断逻辑

```
优化任务：修改 agent.py 第 142 行的失败判断逻辑。
当前：if "错误" in str(result) or "❌" in str(result)
问题：会误判包含这些字符的正常返回
改为：if str(result).startswith(('错误：', '执行失败', '执行异常'))
这样只检查特定的错误格式开头。修改后提交到 GitHub 并更新版本号到 1.7.4。
```

---

## 预期效果

修复后：
1. ✅ JARVIS 不会因为 API 慢而卡住
2. ✅ 工具返回的正常内容不会被误判为失败
3. ✅ 保留试错和自我反思能力
4. ✅ 可以完成复杂的长时间任务

---

**文档生成时间**: 2026-01-30
**下一步**: 让 JARVIS 按顺序执行这两个修复任务
