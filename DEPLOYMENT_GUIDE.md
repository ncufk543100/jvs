# 贾维斯部署和使用指南

## 📦 项目信息

- **项目名称**：JARVIS（贾维斯）
- **当前版本**：v1.55.18
- **GitHub仓库**：https://github.com/ncufk543100/jarvis
- **项目类型**：智能AI助理系统

## 🚀 快速部署

### 1. 克隆项目

```bash
git clone https://github.com/ncufk543100/jarvis.git
cd jarvis
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

**依赖包：**
- fastapi>=0.100.0
- uvicorn>=0.23.0
- pydantic>=2.0.0
- openai>=1.0.0

### 3. 启动服务

```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

### 4. 访问界面

打开浏览器访问：`http://localhost:8000`

## 🎨 UI界面特性

### 深蓝色主题设计（v1.55.18）

**视觉特点：**
- 深蓝到深灰的渐变背景
- 半透明卡片设计
- 蓝色光晕效果
- 红色发送按钮

**功能模块：**
1. 🚀 **代码进化** - 分析和优化代码架构
2. 🌐 **全网搜寻** - 实时检索全球网络信息
3. 🏗️ **自治工程** - 独立管理Git仓库和Shell执行
4. 🧩 **多维接入** - 支持企业微信等多平台集成

## 🔧 配置说明

### Git配置

项目已配置自动化版本管理系统：

```bash
# 使用自动同步脚本
./auto_sync.sh "功能说明"
```

### 版本管理规则

- **格式**：x.y.z（百进制）
- **范围**：1.0.0 到 1.9.9
- **增量**：每次更新 +0.0.1

详见：`VERSION_WORKFLOW.md`

## 📁 项目结构

```
jarvis/
├── server.py              # FastAPI服务器
├── agent.py               # AI代理核心
├── ui.html                # Web界面（深蓝主题）
├── executor.py            # 任务执行器
├── llm.py                 # LLM接口
├── memory_manager.py      # 记忆管理
├── self_modify.py         # 自我修改功能
├── logic/                 # 逻辑引擎
│   └── family_analysis.py # 家庭伦理分析
├── memory/                # 长期记忆存储
├── prompts/               # 提示词模板
├── scripts/               # 自动化脚本
├── VERSION.json           # 版本配置
├── VERSION_WORKFLOW.md    # 版本管理流程
├── auto_sync.sh           # 自动同步脚本
└── README.md              # 项目说明
```

## 🛠️ 核心功能

### 1. 文件操作
- 读取、写入、搜索文件
- 扫描项目结构
- 生成项目地图

### 2. Shell执行
- 执行系统命令
- 运行Python代码
- 安全沙箱保护

### 3. Git操作
- 查看状态和历史
- 自动提交和推送
- 版本管理

### 4. 智能规划
- AI理解自然语言
- 动态任务规划
- 多轮对话记忆

### 5. 自我修改
- 安全的代码修改
- 测试验证
- 回滚机制

## 🔄 开发工作流

### 标准流程

1. **修改代码** - 在本地进行开发
2. **测试验证** - 确保功能正常
3. **立即同步** - 使用 `./auto_sync.sh "说明"`
4. **验证推送** - 检查GitHub确认

### 示例

```bash
# 修改功能后立即同步
./auto_sync.sh "添加新功能：智能代码分析"

# 修复bug后立即同步
./auto_sync.sh "修复：内存管理bug"

# 更新文档后立即同步
./auto_sync.sh "更新：部署指南文档"
```

## 📊 API端点

### 基础端点

- `GET /` - Web界面
- `POST /run` - 执行AI任务
- `GET /events` - 获取事件日志
- `GET /health` - 健康检查
- `GET /report` - 获取报告

### 自我修改端点

- `POST /self-modify/start` - 启动修改会话
- `GET /self-modify/status` - 获取会话状态
- `POST /self-modify/read` - 读取临时文件
- `POST /self-modify/modify` - 修改临时文件
- `POST /self-modify/test` - 运行测试
- `POST /self-modify/apply` - 应用修改
- `POST /self-modify/rollback` - 回滚修改
- `POST /self-modify/end` - 结束会话
- `POST /self-modify/restart` - 重启服务器

## 🔐 安全特性

1. **安全删除** - 删除文件需要用户确认
2. **沙箱执行** - Shell命令在受控环境中运行
3. **修改验证** - 自我修改前进行测试
4. **回滚机制** - 支持快速回滚到之前状态

## 📝 注意事项

### 必须遵守

- ✅ 每个功能修改后立即同步
- ✅ 提交说明清晰描述改动
- ✅ 确保代码可运行后再同步
- ✅ 同步前检查git status

### 严禁操作

- ❌ 批量提交多个功能
- ❌ 延迟同步到最后推送
- ❌ 跳过版本号更新
- ❌ 使用模糊的提交说明

## 🐛 故障排查

### 服务器启动失败

```bash
# 检查端口占用
lsof -i :8000

# 杀死占用进程
kill -9 <PID>

# 重新启动
uvicorn server:app --host 0.0.0.0 --port 8000
```

### Git推送失败

```bash
# 拉取最新代码
git pull origin main --rebase

# 重新推送
git push origin main
```

### 依赖问题

```bash
# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

## 📞 技术支持

- **GitHub Issues**：https://github.com/ncufk543100/jarvis/issues
- **项目文档**：查看仓库中的各类MD文件

## 📜 更新日志

### v1.55.18 (2026-01-29)
- 升级UI界面为深蓝色主题设计
- 优化用户体验和视觉效果
- 更新功能卡片描述

### v1.55.17 (2026-01-29)
- 添加版本管理系统
- 创建自动化同步脚本
- 建立版本管理工作流程

### v1.55.16
- 基于中国家庭星谱项目进化
- 添加家庭伦理分析引擎

---

**贾维斯心智版本：v1.55.18**  
**"Manus 为骨，贾维斯为魂。"**
