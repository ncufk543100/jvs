# 贾维斯2号部署指南

## 版本信息
- **版本**: v1.0.2
- **更新日期**: 2026-01-30
- **打包文件**: jarvis2-v1.0.2-deploy.tar.gz (20MB)

## 系统要求

### Windows
- Windows 10/11
- Node.js 22.x
- pnpm 9.x
- 至少 2GB 可用磁盘空间

### 可选（本地AI）
- Ollama (用于本地deepseek-r1:14b模型)
- 端口11434可用

## 部署步骤

### 1. 解压部署包

```cmd
# 解压到任意目录
tar -xzf jarvis2-v1.0.2-deploy.tar.gz
cd jarvis2
```

### 2. 创建工作目录

```cmd
# 创建贾维斯工作区
mkdir D:\jarvisbox
mkdir D:\jarvisbox\logs
mkdir D:\jarvisbox\imported
```

### 3. 安装依赖

```cmd
# 安装pnpm（如果未安装）
npm install -g pnpm

# 安装项目依赖（自动下载Windows版本）
pnpm install
```

**注意**: 首次安装需要下载约500MB的依赖包，包括：
- AI模型库
- 向量数据库
- TypeScript编译器
- 其他工具

### 4. 配置API密钥

创建 `.env` 文件：

```env
# DeepSeek API（优先级2）
DEEPSEEK_API_KEY=sk-c4c0f92e2c584c18a803c1f64358de9d

# OpenAI兼容API（优先级3）
OPENAI_API_KEY=sk-vHNGa7h38ToLtIPD0cF385A93226494190371aAaDe30434f
OPENAI_BASE_URL=https://api.openai.com/v1

# Ollama本地（优先级1，可选）
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=deepseek-r1:14b
```

### 5. 构建项目

```cmd
pnpm build
```

### 6. 启动贾维斯2号

```cmd
# 开发模式
pnpm dev

# 生产模式
pnpm start
```

## 验证安装

### 测试文件系统权限守卫

```cmd
# 运行权限测试
pnpm test:permissions
```

预期输出：
```
=== 文件系统权限守卫测试 ===

测试1: 检查路径是否在可写区域
  D:\jarvisbox\test.txt: ✅ 可写
  C:\Windows\system32\config.ini: ❌ 只读

测试2: 检查文件操作权限
  2a. 读操作（应该都允许）: ✅
  2b. 写操作（只允许可写区域）: ✅

=== 测试完成 ===
```

### 测试AI连接

```cmd
# 测试Ollama本地连接
curl http://127.0.0.1:11434/api/tags

# 测试DeepSeek API
# （将在首次运行时自动测试）
```

## 使用说明

### 启动后访问

浏览器打开：`http://localhost:3000`

### 工作区说明

- **可写区域**: `D:\jarvisbox\`
  - 贾维斯可以在此目录内自由创建、修改、删除文件
  
- **只读区域**: 系统其他所有区域
  - 可以读取和使用
  - 不能直接修改
  - 如需修改，会自动提示复制到工作区

### 违规日志

如果贾维斯尝试修改只读区域的文件，会记录到：
```
D:\jarvisbox\logs\permission_violations.log
```

## 故障排除

### 问题1: pnpm install失败

**解决方案**:
```cmd
# 清理缓存
pnpm store prune

# 重新安装
pnpm install --force
```

### 问题2: Ollama连接失败

**检查**:
1. Ollama是否运行：`ollama list`
2. 端口是否占用：`netstat -ano | findstr 11434`
3. 模型是否下载：`ollama pull deepseek-r1:14b`

**解决方案**:
- 如果Ollama不可用，贾维斯会自动降级到DeepSeek API

### 问题3: 权限守卫不工作

**检查**:
1. `D:\jarvisbox` 目录是否存在
2. `FILESYSTEM_PERMISSIONS.json` 中 `enforcement.enabled` 是否为 `true`

**解决方案**:
```cmd
# 重新创建工作目录
mkdir D:\jarvisbox
mkdir D:\jarvisbox\logs
```

## 卸载

```cmd
# 1. 停止服务
# Ctrl+C 或关闭终端

# 2. 删除依赖
cd jarvis2
pnpm store prune

# 3. 删除项目
cd ..
rmdir /s /q jarvis2

# 4. 删除工作区（可选）
rmdir /s /q D:\jarvisbox
```

## 更新

### 从v1.0.1升级到v1.0.2

```cmd
# 1. 备份工作区
xcopy D:\jarvisbox D:\jarvisbox_backup /E /I

# 2. 解压新版本
tar -xzf jarvis2-v1.0.2-deploy.tar.gz

# 3. 重新安装依赖
cd jarvis2
pnpm install

# 4. 重新构建
pnpm build

# 5. 启动
pnpm start
```

## 技术支持

- GitHub: https://github.com/ncufk543100/jvs
- 文档: 查看 `README.md` 和 `FILESYSTEM_GUARD_README.md`
- 问题反馈: 提交 GitHub Issue

## 版本历史

- **v1.0.2** (2026-01-30): 添加文件系统权限守卫
- **v1.0.1** (2026-01-30): 初始版本
