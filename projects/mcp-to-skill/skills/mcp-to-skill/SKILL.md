---
name: mcp-to-skill
description: |
  将任意 MCP server 转换为独立的 skill 文件包，生成后零运行时依赖（不依赖 MCP 进程）。
  触发场景：用户说"把这个 MCP 转成 skill"、"我不想用 MCP 了"、"把 X MCP 包装成 skill"、
  "MCP 太重了"、"把 MCP 的能力变成 skill"。
  做什么：连接 MCP server 提取 tool schema，分析源码推断等价 Bash 命令，
  生成可直接使用的 skill 包并注册到 agent，可选询问是否移除原 MCP。
  不做什么：不适用于"调用某个 MCP tool 完成任务"（那是直接使用 MCP，不是转换）；
  不适用于"把已有 Bash 脚本包成 skill"（使用 skill-creator）；不执行 MCP 的业务逻辑。
  可选依赖：skill-creator（提升生成的 SKILL.md 质量）。
---

# mcp-to-skill

将 MCP server 转换为零依赖的 skill 包，使 AI agent 可通过 Bash 命令直接调用，
无需启动 MCP 进程、无需全量注入工具定义。

---

## 步骤一：获取 MCP 信息

根据用户输入判断分支：

**A — 用户提供了命令字符串 / 本地路径 / URL：**
确认命令可用，继续步骤二。

**B — 用户粘贴了 tool schema JSON：**
将 JSON 保存到临时文件，**跳过步骤二**，直接进入步骤三。
使用 Write 工具将用户粘贴的 JSON 写入 `/tmp/mcp-schema-input.json`。
进入步骤三时，使用 `--schema-json /tmp/mcp-schema-input.json`。

**C — 用户未指定，想从已注册 MCP 中选择：**
列出当前 agent 已注册的 MCP，让用户选择。
在 Claude Code 中：运行 `claude mcp list`

---

## 步骤二：运行 mcp_inspector.py（仅非 B 类输入：A 或 C）

定位 `mcp_inspector.py`：它与本 SKILL.md 在同一目录。
框架加载本 skill 时会在 system-reminder 中提供 `Base directory for this skill`，
用该路径构建脚本路径：

```bash
# 确认 mcp SDK 已安装
pip show mcp > /dev/null 2>&1 || pip install mcp

# SKILL_DIR = system-reminder 中 "Base directory for this skill" 的值
INSPECTOR_PATH="$SKILL_DIR/mcp_inspector.py"

python "$INSPECTOR_PATH" "<MCP命令>" --output /tmp/mcp-inspector-output.json
```

输出示例：
```
写入 /tmp/mcp-inspector-output.json：12 个 tool，源码：/tmp/mcp-to-skill-cache/server-github
```

使用 Read 工具读取 `/tmp/mcp-inspector-output.json`，获取：`server_name`、`source_path`（可能为 null）、`tools[]`。

---

## 步骤三：AI 分析，推断等价命令

读取 inspector 输出（或步骤一 B 的 schema 文件）。

**若 source_path 非 null：**
用 Read / Grep 工具读取源码文件，定位每个 tool 对应的实现代码，提取：
- HTTP endpoint（URL、method、headers、body 结构）
- 或 CLI 命令调用模式

**若 source_path 为 null：**
仅凭 tool 的 `description` 和 `inputSchema` 推断合理的等价命令。

为每个 tool 写出命令草稿，附置信度标记：
- `[VERIFIED]` — 源码中有明确 API 对应（仅在有源码时出现）
- `[INFERRED]` — AI 推断，逻辑合理但未测试（source_path 为 null 时最高为此级）
- `[TODO]` — 无法自动生成，留占位说明

---

## 步骤四：测试只读命令

对每个 `[INFERRED]` 且为只读操作（GET 请求、查询类）的命令，用 Bash 工具执行测试：

- 测试通过 → 升级为 `[VERIFIED]`
- 测试失败 → 保持 `[INFERRED]`，在命令上方用注释记录失败原因
- 写操作（POST/PUT/DELETE、文件修改）**跳过测试**，保持 `[INFERRED]`
- `[TODO]` 项不参与测试

---

## 步骤五：生成 skill 包

在用户当前工作目录（或用户指定路径）下创建 skill 目录，结构如下：

```
<mcp-server-name>/
  SKILL.md
  config.json
  helpers/          （按需创建，不预先创建空目录）
    tools-extended.md  （tool 数量 > 8 时）
    <tool>.py / <tool>.sh  （逻辑复杂无法压缩为单条命令时）
```

**渐进式披露规则：**
- tool 数量 ≤ 8：所有工具写入 SKILL.md 工具速查节
- tool 数量 > 8：SKILL.md 只列最常用 8 个，其余写入 `helpers/tools-extended.md`，SKILL.md 末尾注明"更多工具见 helpers/tools-extended.md"

**SKILL.md frontmatter 模板：**

```yaml
---
name: <server-name>
description: |
  [何时用]：<根据 tool descriptions 总结的使用场景>
  [做什么]：<核心能力概括>
  [不做什么]：<明确排除的场景>
  [依赖什么]：<运行时依赖，若零依赖则写"无运行时依赖">
---
```

**config.json 模板：**

```json
{
  "endpoint": "<从源码提取的 base URL，或留空占位>",
  "auth_token": ""
}
```

重要：config.json 在每次工具调用时读取（非启动时缓存）。若 auth_token 为空，调用需认证的工具前必须提示用户填写，不得使用空 token 继续。

**若 agent 上下文中已加载 skill-creator：**
将分析结果（tool 列表 + 推断命令 + 置信度）传给 skill-creator，由其生成 SKILL.md。

---

## 步骤六：注册 skill 到当前 AI agent

目标：将生成的 skill 目录注册到当前 AI agent，使其立即可用。按顺序探查并执行最合适的方式：

1. 检测 `npx skills` 是否可用：
   ```bash
   which npx && npx skills --version 2>/dev/null
   ```
   若可用：`npx skills add <skill-path> -g -y`

2. 检测是否为 Claude Code 环境：
   ```bash
   claude --version 2>/dev/null
   ```
   若可用：软链接到 `~/.claude/skills/<skill-name>`：
   ```bash
   ln -sf <skill-path> ~/.claude/skills/<skill-name>
   ```
   注意：`/add-dir` 是交互式 slash command，不能通过 Bash 调用。

3. 均不适用时：输出 skill 路径，告知用户手动注册：
   > "Skill 已生成到 `<path>`，请将该目录注册到你使用的 AI agent。
   > Claude Code 用户：运行 `/add-dir <path>`
   > npx skills 用户：运行 `npx skills add <path> -g`"

---

## 步骤七：询问是否移除原 MCP（可选）

仅在步骤一为 A 或 C 类输入（非粘贴 schema）时提示：

> "MCP `<server-name>` 已转换为 skill，是否从你使用的 AI agent 中移除该 MCP 配置？"

- 用户确认 → 协助执行移除操作（agent 自行判断如何移除）
- 用户拒绝或无响应 → 跳过，skill 与 MCP 可并存
