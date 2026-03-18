# mcp-to-skill

将任意 MCP server 转换为零运行时依赖的 skill 包，AI agent 通过 Bash 命令直接调用工具，无需启动 MCP 进程。

## 安装

```bash
ln -sf /path/to/mcp-to-skill ~/.claude/skills/mcp-to-skill
```

## 依赖

```bash
pip install mcp
```

## 使用

在 Claude Code 中描述你的需求，skill 自动执行：

```
把 npx -y @modelcontextprotocol/server-github 转成 skill
```

```
把这个 MCP 的 schema JSON 转成 skill：{ ... }
```

```
把我已注册的 MCP 里的 filesystem 转成 skill
```

## 转换流程

| 步骤 | 操作 |
|------|------|
| 1 | 获取 MCP 信息（命令/路径/粘贴 schema/已注册列表） |
| 2 | 运行 `mcp_inspector.py` 提取工具 schema |
| 3 | 分析源码，推断等效 Bash/HTTP 命令 |
| 4 | 测试只读命令，验证可用性 |
| 5 | 生成 skill 包（SKILL.md + config.json + secrets.json） |
| 6 | 注册到当前 AI agent |
| 7 | 询问是否移除原 MCP 配置 |

## 生成的 skill 结构

```
<mcp-server-name>/
  SKILL.md              # skill 主文件
  config.json           # 公开配置（可提交）
  secrets.json          # 密钥（已 gitignore）
  secrets.json.example  # 密钥模板（可提交）
  .gitignore
  helpers/              # 工具超过8个时自动生成
    tools-extended.md
```

## 命令置信度标记

生成的 SKILL.md 中每条命令带有置信度：

- `[VERIFIED]` — 经源码确认或测试通过
- `[INFERRED]` — AI 推断，逻辑合理但未测试
- `[TODO]` — 无法自动生成，含占位说明
