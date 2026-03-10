# personal-notes

个人 Obsidian vault 笔记管理 skill，支持多类内容自动路由归档。

## Skills

| Skill | 描述 |
|-------|------|
| `personal-notes-skill` | 个人笔记主 skill，路由内容到 PARA/Finance/Paper/Personal 各模块 |

## 安装

```bash
cp -r projects/personal-notes/skills/personal-notes-skill ~/.claude/skills/my-notes
```

安装后编辑 `~/.claude/skills/my-notes/config.json`，填入你的 vault 路径：

```json
{
  "vault_root": "/path/to/your/obsidian/vault",
  "vault_guide": "PARA/vault-guide.md"
}
```

## 使用

在 Claude 对话中直接描述要归档的内容，skill 会自动路由：

| 内容类型 | 目标 |
|---------|------|
| 技术文章 / 博客 URL | `PARA/Resources/` 归档 |
| arXiv 论文 | `Paper/{领域}/{年}/{月}/` |
| 金融研报 / 市场观察 | `Finance/stock/YYYY-M.md` |
| Todo / 快速想法 | `Personal/todo.md`（支持 Reminder 插件时间格式） |
| 健康 / 锻炼记录 | `Personal/` 对应文件 |

## 依赖

- [obsidian-cli](https://help.obsidian.md/cli)（需安装并保持 Obsidian 运行）
- Obsidian 社区插件：**Reminder**（可选，用于 todo 定时提醒）
