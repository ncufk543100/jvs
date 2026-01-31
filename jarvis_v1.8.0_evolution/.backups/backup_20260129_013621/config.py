from pathlib import Path

# 允许 Agent 操作的唯一目录（项目目录）
PROJECT_ROOT = Path("/home/ubuntu/clawedbot").resolve()

# 允许调用的系统命令（白名单前缀）
ALLOWED_COMMANDS = [
    "npm", "pnpm", "yarn",
    "node",
    "git",
    "wx",            # 微信开发者工具 CLI
    "npx",
    "python",
    "powershell",
    "cmd"
]
