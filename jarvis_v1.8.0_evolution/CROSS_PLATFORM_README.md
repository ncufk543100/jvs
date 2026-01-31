# 跨平台使用指南

## Windows 11 安装步骤
1. 安装 Python 3.8+
2. 克隆仓库: `git clone https://github.com/ncufk543100/clawedbot.git`
3. 安装依赖: `pip install -r requirements.txt`
4. 运行: `uvicorn server:app --host 0.0.0.0 --port 8000`

## Linux 安装步骤
1. 安装 Python 3.8+
2. 克隆仓库: `git clone https://github.com/ncufk543100/clawedbot.git`
3. 安装依赖: `pip install -r requirements.txt`
4. 运行: `uvicorn server:app --host 0.0.0.0 --port 8000`

## 跨平台特性
- ✅ 使用 pathlib 处理路径，兼容 Windows/Linux
- ✅ 使用 subprocess 替代 shell 命令
- ✅ 统一的进程管理接口
- ✅ 增强的测试机制确保功能正常