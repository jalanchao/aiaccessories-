# AIAccessories-

个人 Claude Skills 集合，将个人工作流和工具封装为可复用的 AI Agent skill。

> **对应关系：** [AIAccessories](../AIAccessories) 存放公司/团队项目；本仓库存放个人项目。

## 项目列表

| 项目 | Skills | 描述 |
|------|--------|------|
| [personal-notes](./projects/personal-notes/) | `my-notes` | 个人 Obsidian vault 笔记管理，支持 PARA/Finance/Paper/Personal 多模块路由归档 |
| [mcp-to-skill](./projects/mcp-to-skill/) | `mcp-to-skill` | 将任意 MCP server 转换为零运行时依赖的 skill 包，自动提取工具 schema 并生成可复用 skill |

## 快速开始

每个项目的 `skills/` 目录下即为可直接使用的 Claude Skill：

```bash
# 安装 personal-notes skill
cp -r projects/personal-notes/skills/personal-notes-skill ~/.claude/skills/my-notes

# 按项目 README 填写 config.json 后即可使用
```

## 仓库结构

```
AIAccessories-/
├── projects/
│   ├── personal-notes/    ← Obsidian 笔记管理
│   ├── mcp-to-skill/      ← MCP → Skill 转换工具
│   └── {project-name}/
│       ├── skills/        ← Claude Skill 文件（直接可用）
│       ├── docs/plans/    ← 设计文档与实现计划（按需）
│       └── README.md      ← 安装说明与使用示例
└── README.md
```

## 新增项目

在 `projects/` 下创建同样结构的目录即可。
