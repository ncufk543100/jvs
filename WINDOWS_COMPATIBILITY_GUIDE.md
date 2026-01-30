# Windows 11 兼容性指南

## 安装要求
- Python 3.8+
- Git

## 快速开始
```bash
git clone https://github.com/ncufk543100/clawedbot.git
cd clawedbot
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8000
```

## 平台特定说明
- 所有路径使用pathlib处理，兼容Windows和Linux
- 进程管理使用跨平台API
- 文件操作使用Python原生实现，避免平台相关命令

## 测试验证
在Windows 11上运行测试确保功能正常