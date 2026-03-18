# personal-notes-skill

个人 Obsidian vault 笔记管理 skill，自动识别内容类型并路由到对应归档工作流。

## 安装

```bash
cp -r /path/to/personal-notes-skill ~/.claude/skills/my-notes
```

编辑 `~/.claude/skills/my-notes/config.json`，填入 vault 路径：

```json
{
  "vault_root": "/path/to/your/obsidian/vault",
  "vault_guide": "PARA/vault-guide.md"
}
```

## 内容路由

| 输入类型 | 目标工作流 | 归档位置 |
|---------|-----------|---------|
| 技术文章 / 博客 / 视频字幕 | PARA 总结（7步） | `PARA/Resources/` |
| arXiv URL / 学术论文 | Paper 精细归档 | `Paper/{领域}/{年}/{月}/` |
| 金融研报 / 市场观察 / 投资记录 | Finance | `Finance/stock/YYYY-M.md` |
| 快速想法 / todo | Personal | `Personal/todo.md` |
| 待读链接 | TEMP | `TEMP/see_this.md` |
| 健康 / 锻炼 / 生活记录 | Personal | `Personal/` 对应文件 |

## Todo 格式

使用 Obsidian Tasks 插件兼容格式：

```
- [ ] {内容} 📅 YYYY-MM-DD {优先级} {#标签}
```

- 截止日期：`📅 2026-03-22`
- 优先级：`⏫` 紧急重要 / `🔼` 重要 / 无=普通 / `🔽` 低优先级
- 标签：`#work` / `#work/项目名` / `#life`

已完成且早于7天的条目可归档到 `Personal/todo-done/YYYY-MM.md`。

## 自组织能力

每次操作后自动更新 `vault-guide.md`，积累：
- 目录结构变更
- 分类决策先例
- 用户确认的命名约定

vault-guide.md 随 vault 同步到所有设备，知识持续沉淀。

## 依赖

- `obsidian:obsidian-cli` — 文件读写（不可用时自动 fallback 到 Read/Write 工具）
- `obsidian:obsidian-markdown` — Obsidian 格式语法
- `obsidian:defuddle` — URL 内容提取
- Obsidian 社区插件：**Tasks**（todo 视图）
