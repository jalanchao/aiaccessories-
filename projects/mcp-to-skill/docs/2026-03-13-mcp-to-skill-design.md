# mcp-to-skill Design Spec

**日期**: 2026-03-13
**状态**: 待实现

---

## 概述

`mcp-to-skill` 是一个 skill，用于将任意 MCP server 转换为独立的 skill 包。转换后的 skill 零运行时依赖（不依赖 MCP 进程、不依赖 mcporter），可被任意 AI agent 使用。

**核心动机**：
- MCP 在 agent 上下文中过重——所有工具定义一次性全量注入
- MCP 不符合渐进式披露原则
- MCP 调用不一定需要 agent，直接 Bash/curl 更轻量

---

## 输入

支持两种输入场景，执行路径不同：

1. **已注册 MCP**：从当前 AI agent 的 MCP 配置中选取（如 `claude mcp list`），完整走步骤①②③④
2. **任意 MCP（命令字符串/URL/本地路径）**：完整走步骤①②③④
3. **直接粘贴 tool schema JSON**：**跳过步骤②**，直接进入步骤③（AI 分析），`source_path` 为 null

---

## 执行流程

```
① 获取 MCP 信息
   ├── 已注册：列出可用 MCP，用户选择
   ├── 任意输入：接受命令字符串 / URL / 本地路径
   └── 粘贴 schema JSON → 跳至步骤③

② mcp_inspector.py（脚本主导，仅在非 schema 粘贴场景执行）
   ├── 通过 MCP JSON-RPC 协议连接 server（stdio 或 HTTP/SSE）
   ├── 调用 tools/list 提取所有 tool schema
   ├── 识别 npm/pip 包名
   └── 尝试拉取源码（npm pack / GitHub API / 本地路径）
   输出：inspector.json（见下方 Schema 定义）

   源码拉取失败处理：
   - 私有包 / 网络受限 / 无 GitHub 仓库：source_path 置为 null，继续执行
   - 步骤③中 AI 仅凭 tool schema（description + inputSchema）推断命令
   - 无源码时所有命令置信度上限为 [~ INFERRED]，不会出现 [✓ VERIFIED]

③ AI 分析（AI 主导）
   ├── 若 source_path 非 null：读取源码文件，精确提取 HTTP 调用 / CLI 调用模式
   ├── 若 source_path 为 null：仅凭 tool description + inputSchema 推断
   └── 为每个 tool 输出等价 Bash/curl 命令草稿，附置信度标记：
       [✓ VERIFIED]  — 源码中有明确 API 对应（仅在有源码时出现）
       [~ INFERRED]  — AI 推断，逻辑合理但未测试
       [! TODO]      — 无法自动生成，需人工补全，留占位说明

④ 测试命令可用性（AI 主导 + Bash 兜底）
   测试策略：
   - 只测试 [~ INFERRED] 且为只读操作（GET 请求、查询类命令）的命令
   - 写操作（POST/PUT/DELETE、文件修改）跳过测试，保持 [~ INFERRED] 标记
   - 测试通过 → 升级为 [✓ VERIFIED]
   - 测试失败（命令错误、认证缺失等）→ 保持 [~ INFERRED] 并在命令注释中记录失败原因
   - [! TODO] 项不参与测试

⑤ 生成 skill 包
   ├── 若 agent 上下文中已加载 skill-creator，委托其生成 SKILL.md
   └── 否则按项目规范直接生成（见下方"生成的 skill 包规范"）

   工具数量与渐进式披露：
   - tool 数量 ≤ 8：所有工具写入 SKILL.md 工具速查
   - tool 数量 > 8：SKILL.md 只列最常用的 8 个（依据 description 判断使用频率），
     其余工具写入 helpers/tools-extended.md，SKILL.md 末尾注明"更多工具见 helpers/tools-extended.md"

⑥ 注册 skill 到当前 AI agent
   目标：将生成的 skill 目录注册到当前 AI agent，使其立即可用。

   探查顺序（agent 自行判断并执行最合适的方式）：
   1. 检测 `npx skills` 是否可用 → `npx skills add <skill-path> -g -y`
   2. 检测是否为 Claude Code 环境 → `/add-dir <skill-path>` 或软链接到 `~/.claude/skills/`
   3. 均不适用 → 输出 skill 路径，告知用户手动注册，并说明常见注册方式

⑦ 询问是否移除原 MCP（可选步骤，默认不移除）
   提示："MCP [name] 已转换为 skill，是否从你使用的 AI agent 中移除该 MCP 配置？"
   - 用户确认后执行移除
   - 用户拒绝或无响应 → 跳过，skill 与 MCP 并存

---

## inspector.json Schema

```json
{
  "server_name": "github",
  "package": "@modelcontextprotocol/server-github",  // null 若无法识别
  "source_path": "/tmp/mcp-to-skill-cache/server-github/",  // null 若拉取失败
  "tools": [
    {
      "name": "search_repositories",
      "description": "Search for GitHub repositories",
      "inputSchema": {
        "type": "object",
        "properties": {
          "query": { "type": "string" }
        },
        "required": ["query"]
      }
    }
  ]
}
```

---

## 文件结构

```
projects/mcp-to-skill/
  docs/
    2026-03-13-mcp-to-skill-design.md   # 本文件
  skills/
    mcp-to-skill/
      SKILL.md                           # skill 主文件
      mcp_inspector.py                   # 脚本层：MCP 协议 + 源码拉取
```

---

## mcp_inspector.py 职责（脚本层）

| 功能 | 说明 |
|------|------|
| `connect(command)` | 通过 stdio/HTTP 连接 MCP server，支持任意命令字符串 |
| `list_tools()` | JSON-RPC `tools/list`，返回完整 schema |
| `detect_package()` | 从进程命令推断 npm/pip 包名，失败返回 null |
| `fetch_source()` | npm pack / GitHub API / 本地路径，失败返回 null（不抛出异常） |
| 输出 | `inspector.json`，source_path/package 失败时置 null |

脚本只负责确定性操作，不含任何 AI 逻辑。所有失败以 null 值表示，不中断流程。

---

## 生成的 skill 包规范

### SKILL.md 结构

```markdown
---
name: <mcp-name>
description: <何时用 / 做什么 / 不做什么 / 依赖什么>
---

# <MCP Name>

## 配置
读取同目录 config.json 获取 endpoint、认证信息。
若 auth_token 为空，执行需认证的操作前必须提示用户填写后重试，不得使用空 token 继续。

## 工具速查

### tool_name
[✓ VERIFIED]
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.example.com/endpoint?param={value}"
```

### write_tool
[~ INFERRED] 写操作未测试
```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -d '{"key": "{value}"}' \
  "https://api.example.com/resource"
```

### another_tool
[! TODO] 需要手动补全：无法从 schema 推断底层 API，请参考原 MCP 文档
```

### config.json 结构

```json
{
  "endpoint": "https://api.example.com",
  "auth_token": ""
}
```

config.json 在每次工具调用时读取（非启动时缓存），确保 token 更新后立即生效。

### helpers/（按需生成）

- 工具逻辑无法压缩为单条 Bash 命令时 → 生成 `helpers/<tool>.py` 或 `helpers/<tool>.sh`
- tool 数量 > 8 时 → 生成 `helpers/tools-extended.md`
- 遵循渐进式披露原则，不预先生成空 helpers/

---

## 依赖声明

- **mcp Python SDK**：`pip install mcp`（mcp_inspector.py 运行时需要）
- **skill-creator**（可选）：若已加载，委托生成 SKILL.md 以提升质量
- 生成的 skill **零运行时依赖**（不依赖 MCP 进程、不依赖 mcporter）

---

## SKILL.md description 草稿

```
将任意 MCP server 转换为独立的 skill 文件包，生成后零运行时依赖。
触发场景：用户说"把这个 MCP 转成 skill"、"我不想用 MCP 了"、
"把 X MCP 包装成 skill"、"MCP 太重了"、"把 MCP 的能力变成 skill"。
做什么：连接 MCP server 提取 tool schema，分析源码推断等价 Bash 命令，
生成可直接使用的 skill 包并注册到 agent，可选询问是否移除原 MCP。
不做什么：
- 不适用于"调用某个 MCP tool 完成任务"（那是直接使用 MCP，不是转换）
- 不适用于"把已有 Bash 脚本包成 skill"（使用 skill-creator）
- 不执行 MCP 的业务逻辑
可选依赖：skill-creator（提升 SKILL.md 质量）。
```

---

## 自检清单

- [x] 空上下文测试：执行流程含完整分支说明，全新 agent 可无歧义执行
- [x] Description 路由测试：description 包含触发场景 + 明确排除场景，防止误路由
- [x] 依赖声明测试：skill-creator 依赖仅在 description 中声明，未在流程中硬编码调用
