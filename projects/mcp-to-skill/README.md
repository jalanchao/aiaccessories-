# mcp-to-skill

将任意 MCP server 转换为零运行时依赖的 skill 包。

## 安装

    ln -sf $(pwd)/skills/mcp-to-skill ~/.claude/skills/mcp-to-skill

## 依赖

    pip install mcp

## 使用

在 Claude Code 中触发：
> "把 `npx -y @modelcontextprotocol/server-github` 转成 skill"

详见 [设计文档](docs/2026-03-13-mcp-to-skill-design.md)
