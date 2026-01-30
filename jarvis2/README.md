# 贾维斯2号 (JARVIS 2)

**版本**: v1.0.2  
**基于**: OpenClaw 2026.1.29  
**更新日期**: 2026-01-30

## 简介

贾维斯2号是基于OpenClaw的智能助手，支持技能系统和自我进化能力。

### 核心特性

1. **技能系统**
   - 模块化技能管理（SKILL.md格式）
   - 自动技能匹配和加载
   - 渐进式披露（元数据→指令→资源）

2. **多模型支持**
   - **优先级1**: Ollama本地 (deepseek-r1:14b)
   - **优先级2**: DeepSeek API (deepseek-chat)
   - **优先级3**: OpenAI兼容 (gpt-5.2)
   - 自动降级切换

3. **自我进化**
   - 任务驱动的自然进化
   - 技能创建和积累
   - 实践中学习和改进

4. **文件系统权限守卫**
   - 仅允许在 `D:\jarvisbox` 目录内修改文件
   - 系统其他区域只读
   - 自动提示和复制功能
   - 违规日志记录

## 安装

### 前置要求

- Node.js ≥ 22
- pnpm (推荐) 或 npm

### 快速开始

```bash
# 安装依赖
pnpm install

# 构建
pnpm build

# 运行
npx openclaw --version
```

## 配置

### 模型配置

编辑 `.openclaw.config.json`:

```json
{
  "models": {
    "providers": {
      "ollama": {
        "baseUrl": "http://127.0.0.1:11434",
        "models": [{"id": "deepseek-r1:14b"}]
      },
      "deepseek": {
        "apiKey": "your-deepseek-api-key",
        "models": [{"id": "deepseek-chat"}]
      },
      "openai": {
        "apiKey": "your-openai-api-key",
        "baseUrl": "https://api.laozhang.ai/v1",
        "models": [{"id": "gpt-5.2"}]
      }
    }
  }
}
```

## 技能系统

### 技能结构

```
skill-name/
├── SKILL.md (必需)
│   ├── YAML frontmatter (name + description)
│   └── Markdown 指令
└── 可选资源
    ├── scripts/      - 可执行脚本
    ├── references/   - 参考文档
    └── assets/       - 输出资源
```

### 创建技能

```bash
# 初始化技能
scripts/init_skill.py my-skill --path skills/public

# 打包技能
scripts/package_skill.py path/to/skill-folder
```

## 与贾维斯1号的区别

| 特性 | 贾维斯1号 | 贾维斯2号 |
|------|----------|----------|
| 架构 | 自定义Python | OpenClaw (Node.js) |
| 技能系统 | 无 | ✅ SKILL.md格式 |
| 自我进化 | 复杂引擎 | 简洁自然 |
| 多模型 | 手动配置 | 自动降级 |
| 社区支持 | 无 | OpenClaw生态 |

## 版本历史

- **v1.0.2** (2026-01-30): 添加文件系统权限守卫，限制写操作仅在D:\jarvisbox目录
- **v1.0.1** (2026-01-30): 初始版本，基于OpenClaw 2026.1.29

## 许可证

MIT License (继承自OpenClaw)

## 相关链接

- [OpenClaw官网](https://openclaw.ai)
- [OpenClaw文档](https://docs.openclaw.ai)
- [贾维斯1号](../README.md)
