# 工具请示机制 (Tool Request Mechanism)

## 核心理念
**主仆有序，权限分明**：贾维斯在需要安装新工具时，必须请示主人，获得批准后方可自行安装。

## 流程设计

### 1. 发现缺少工具
贾维斯在执行任务时，发现缺少某个工具（如浏览器、数据库客户端等）

### 2. 检索本地环境
```python
# 检查工具是否已安装
result = run_shell({"command": "which playwright"})
# 或
result = run_shell({"command": "pip list | grep playwright"})
```

### 3. 请示主人
如果工具不存在，生成confirm事件：
```python
{
    "type": "confirm",
    "message": "主人，我需要安装 playwright 库来实现浏览器自动化功能。\n\n安装命令：pip install playwright\n预计用途：访问网页、分析UI、截图等\n\n是否允许安装？",
    "options": ["允许", "拒绝"]
}
```

### 4. 等待主人决定
- 前端显示确认对话框
- 用户点击"允许"或"拒绝"
- 结果返回给贾维斯

### 5. 执行安装（如果批准）
```python
if user_approved:
    result = run_shell({"command": "pip install playwright"})
    # 验证安装
    verify = run_shell({"command": "playwright --version"})
```

### 6. 继续任务
安装完成后，贾维斯继续执行原任务

## 权限边界

### 贾维斯可以做的：
- ✅ 检测缺少的工具
- ✅ 分析工具用途
- ✅ 请示主人
- ✅ 在获得批准后自己安装
- ✅ 验证安装结果

### 贾维斯不可以做的：
- ❌ 未经请示自己安装
- ❌ 自己决定是否需要某个工具
- ❌ 绕过主人直接下载

### 主人的权力：
- ✅ 批准或拒绝安装请求
- ✅ 了解工具的用途和影响
- ✅ 随时撤销贾维斯的权限

## 实现要点

### 1. 在agent.py中添加请示函数
```python
def request_tool_installation(tool_name, install_command, purpose):
    """请示主人安装工具"""
    emit_event("confirm", {
        "message": f"主人，我需要安装 {tool_name}。\n\n安装命令：{install_command}\n用途：{purpose}\n\n是否允许？",
        "options": ["允许", "拒绝"]
    })
    # 等待用户响应...
```

### 2. 前端UI支持confirm事件
- 显示模态对话框
- 提供"允许"/"拒绝"按钮
- 将结果发送回后端

### 3. 贾维斯的思考模式
当LLM意识到缺少工具时，应该：
1. 先用web_search搜索了解工具
2. 用run_shell检查是否已安装
3. 如果没有，调用request_tool_installation请示
4. 等待批准后再安装

## 示例对话

**贾维斯：** 主人，我发现当前缺少浏览器自动化工具。我需要安装 playwright 库。

**安装命令：** `pip install playwright && playwright install chromium`

**用途：** 
- 访问Manus界面进行UI对比分析
- 实现网页截图功能
- 自动化测试

**预计影响：** 约占用500MB磁盘空间

是否允许安装？

**主人：** 允许

**贾维斯：** 收到！正在安装 playwright...
[执行安装]
安装完成！继续执行任务...

---

**版本：** 1.2.1
**作者：** Manus (教官)
**日期：** 2026-01-29
