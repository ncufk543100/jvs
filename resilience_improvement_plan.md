# JARVIS 韧性执行引擎改进方案

## 问题分析

### 当前问题
1. **直接失败**：工具执行失败后立即返回False，没有重试
2. **忽略输出**：不读取命令输出中的关键信息（如路径、状态）
3. **缺少智能**：不分析错误原因，不尝试替代方案
4. **无法恢复**：遇到问题就终止，缺少自我修复能力

### 具体案例
在自我进化任务中：
- 运行`python evolution_sandbox.py`成功
- 输出包含沙盒路径：`/home/ubuntu/jarvis_evolution/v3.0_*`
- 但JARVIS没有读取输出，直接猜测路径
- 导致后续文件读取失败

## 改进方案

### 1. 工具执行结果增强
修改executor.py，让工具返回更丰富的信息：
```python
{
    "success": bool,
    "result": str,      # 命令输出
    "error": str,
    "metadata": {       # 新增：元数据
        "output_lines": list,
        "extracted_paths": list,
        "extracted_urls": list,
        "exit_code": int
    }
}
```

### 2. 智能输出解析
在agent_final.py中添加输出解析逻辑：
```python
def parse_command_output(output: str, tool: str) -> dict:
    """解析命令输出，提取关键信息"""
    parsed = {
        "paths": [],
        "urls": [],
        "status": None
    }
    
    # 提取路径
    path_pattern = r'/[a-zA-Z0-9_/.-]+'
    parsed["paths"] = re.findall(path_pattern, output)
    
    # 提取URL
    url_pattern = r'https?://[^\s]+'
    parsed["urls"] = re.findall(url_pattern, output)
    
    # 提取状态标识
    if "✅" in output or "成功" in output:
        parsed["status"] = "success"
    elif "❌" in output or "失败" in output:
        parsed["status"] = "failed"
    
    return parsed
```

### 3. 重试机制
```python
def execute_tool_with_retry(tool, params, max_retries=3):
    """带重试的工具执行"""
    for attempt in range(max_retries):
        result = execute(tool, params)
        
        if result.get("success"):
            return result
        
        # 分析失败原因
        error = result.get("error", "")
        
        # 尝试自动修复
        if "文件不存在" in error:
            # 尝试查找文件
            fixed_params = try_find_file(params)
            if fixed_params:
                params = fixed_params
                continue
        
        if "权限不足" in error:
            # 尝试添加sudo
            params["command"] = f"sudo {params['command']}"
            continue
        
        # 无法自动修复，记录并继续
        if attempt < max_retries - 1:
            emit("warning", f"⚠️ 重试 {attempt+1}/{max_retries}: {tool}")
    
    return result
```

### 4. 替代方案策略
```python
def try_alternative_approaches(tool, params, error):
    """尝试替代方案"""
    alternatives = []
    
    if tool == "read_file" and "文件不存在" in error:
        # 方案1：搜索文件
        alternatives.append({
            "tool": "run_shell",
            "params": {"command": f"find /home/ubuntu -name '{os.path.basename(params['path'])}'"}
        })
        
        # 方案2：列出目录
        alternatives.append({
            "tool": "run_shell",
            "params": {"command": f"ls -la {os.path.dirname(params['path'])}"}
        })
    
    return alternatives
```

### 5. 上下文记忆
在agent中维护执行上下文：
```python
self.execution_context = {
    "last_command_output": None,
    "extracted_paths": [],
    "extracted_data": {}
}

# 每次工具执行后更新
def update_context(self, result):
    self.execution_context["last_command_output"] = result.get("result")
    parsed = parse_command_output(result.get("result", ""))
    self.execution_context["extracted_paths"].extend(parsed["paths"])
```

## 实现步骤

### 步骤1：增强executor.py
- 添加输出解析
- 返回元数据

### 步骤2：修改agent_final.py的execute_phase方法
- 添加重试逻辑
- 添加输出解析
- 添加替代方案尝试
- 维护执行上下文

### 步骤3：创建resilience_engine.py模块
- 封装所有韧性执行逻辑
- 提供统一的接口

### 步骤4：测试
- 重新运行自我进化任务
- 验证能否自动找到沙盒路径
- 验证遇到错误时的恢复能力

## 预期效果

改进后，JARVIS应该能够：
1. ✅ 读取`python evolution_sandbox.py`的输出
2. ✅ 提取沙盒路径：`/home/ubuntu/jarvis_evolution/v3.0_*`
3. ✅ 当文件不存在时，自动搜索正确路径
4. ✅ 尝试3次后仍失败才真正失败
5. ✅ 向用户请求帮助而不是直接终止
