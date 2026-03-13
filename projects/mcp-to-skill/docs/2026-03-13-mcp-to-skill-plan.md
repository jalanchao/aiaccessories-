# mcp-to-skill Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 `mcp-to-skill` skill，将任意 MCP server 转换为零运行时依赖的独立 skill 包。

**Architecture:** 两层架构——`mcp_inspector.py`（脚本层，确定性操作：MCP 协议通信 + 源码拉取，输出 `inspector.json`）和 `SKILL.md`（AI 层，分析 inspector.json + 生成目标 skill 包）。脚本层不含 AI 逻辑；AI 层不硬编码外部工具调用。

**Tech Stack:** Python 3.10+, `mcp` SDK (`pip install mcp`), `asyncio`, `subprocess`, npm CLI（用于拉取 npm 包源码）

---

## 文件结构

```
projects/mcp-to-skill/
  docs/
    2026-03-13-mcp-to-skill-design.md   ← 已存在，不修改
    2026-03-13-mcp-to-skill-plan.md     ← 本文件
  skills/
    mcp-to-skill/
      SKILL.md                           ← 新建：skill 主文件（AI 层指令）
      mcp_inspector.py                   ← 新建：脚本层
  tests/
    test_mcp_inspector.py               ← 新建：单元测试
```

---

## Chunk 1: mcp_inspector.py

### Task 1: 搭建项目骨架，写失败测试

**Files:**
- Create: `projects/mcp-to-skill/skills/mcp-to-skill/mcp_inspector.py`
- Create: `projects/mcp-to-skill/tests/test_mcp_inspector.py`

- [ ] **Step 1: 创建 mcp_inspector.py 骨架**

```python
#!/usr/bin/env python3
"""
mcp_inspector.py - MCP server inspector for mcp-to-skill

连接 MCP server，提取 tool schemas，尝试拉取源码。
输出 inspector.json 供 AI 层分析。

用法：
  python mcp_inspector.py "npx -y @modelcontextprotocol/server-github" --output inspector.json
  python mcp_inspector.py --schema-json tools.json --server-name github
"""

import argparse
import asyncio
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional


def detect_package(command: str) -> Optional[str]:
    raise NotImplementedError


def fetch_source(package: Optional[str], local_path: Optional[str] = None) -> Optional[str]:
    raise NotImplementedError


async def connect_and_list_tools(command: str) -> list[dict]:
    raise NotImplementedError


def _write_output(result: dict, output_path: str):
    raise NotImplementedError


def main():
    raise NotImplementedError


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 写 detect_package 的失败测试**

```python
# projects/mcp-to-skill/tests/test_mcp_inspector.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "mcp-to-skill"))

from mcp_inspector import detect_package


def test_detect_package_npx_scoped():
    assert detect_package("npx -y @modelcontextprotocol/server-github") == "@modelcontextprotocol/server-github"


def test_detect_package_npx_unscoped():
    assert detect_package("npx -y mcp-server-filesystem") == "mcp-server-filesystem"


def test_detect_package_unknown_returns_none():
    assert detect_package("python /some/local/server.py") is None


def test_detect_package_node_local_returns_none():
    assert detect_package("node ./dist/index.js") is None
```

- [ ] **Step 3: 运行测试，确认失败**

```bash
cd /Users/j/Projects/AIAccessories-/projects/mcp-to-skill
python -m pytest tests/test_mcp_inspector.py::test_detect_package_npx_scoped -v
```

期望：`FAILED` with `NotImplementedError`

- [ ] **Step 4: 实现 detect_package**

```python
def detect_package(command: str) -> Optional[str]:
    """从命令字符串推断 npm 包名。返回包名或 None。"""
    parts = command.split()
    for i, part in enumerate(parts):
        # npx [-y/--yes] <package>
        if part in ('-y', '--yes') and i + 1 < len(parts):
            candidate = parts[i + 1]
            # 排除本地路径（以 . 或 / 开头）
            if not candidate.startswith('.') and not candidate.startswith('/'):
                return candidate
    return None
```

- [ ] **Step 5: 运行 detect_package 测试，确认通过**

```bash
python -m pytest tests/test_mcp_inspector.py -k "detect_package" -v
```

期望：4 tests PASSED

- [ ] **Step 6: 提交**

```bash
cd /Users/j/Projects/AIAccessories-
git add projects/mcp-to-skill/skills/mcp-to-skill/mcp_inspector.py \
        projects/mcp-to-skill/tests/test_mcp_inspector.py
git commit -m "feat(mcp-to-skill): 添加 mcp_inspector 骨架和 detect_package 实现"
```

---

### Task 2: 实现 fetch_source（源码拉取）

**Files:**
- Modify: `projects/mcp-to-skill/skills/mcp-to-skill/mcp_inspector.py`
- Modify: `projects/mcp-to-skill/tests/test_mcp_inspector.py`

- [ ] **Step 1: 写 fetch_source 失败测试**

```python
import tempfile
import os
from unittest.mock import patch, MagicMock
from mcp_inspector import fetch_source


def test_fetch_source_local_path_exists(tmp_path):
    """本地路径存在时直接返回。"""
    assert fetch_source(None, local_path=str(tmp_path)) == str(tmp_path)


def test_fetch_source_no_package_returns_none():
    """无包名且无本地路径时返回 None。"""
    assert fetch_source(None) is None


def test_fetch_source_npm_failure_returns_none():
    """npm 命令失败时返回 None，不抛出异常。"""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1)
        result = fetch_source("@some/nonexistent-package-xyz-123")
    assert result is None


def test_fetch_source_npm_success_returns_path(tmp_path):
    """npm pack 成功时返回解压后的目录路径。"""
    # 构造真实的缓存目录结构（避免 patch.object(Path, "glob") 全局污染）
    cache_dir = tmp_path / "mcp-to-skill-cache" / "modelcontextprotocol-server-github"
    cache_dir.mkdir(parents=True)
    fake_tgz = cache_dir / "package.tgz"
    fake_tgz.touch()

    def fake_run(cmd, **kwargs):
        # npm pack 创建 tarball，tar 解压成功
        if "npm" in cmd:
            fake_tgz.touch()
        return MagicMock(returncode=0)

    with patch("subprocess.run", side_effect=fake_run), \
         patch("tempfile.gettempdir", return_value=str(tmp_path)):
        result = fetch_source("@modelcontextprotocol/server-github")
    assert result is not None
    assert "modelcontextprotocol-server-github" in result
```

- [ ] **Step 2: 运行失败测试**

```bash
python -m pytest tests/test_mcp_inspector.py -k "fetch_source" -v
```

期望：FAILED with `NotImplementedError`

- [ ] **Step 3: 实现 fetch_source**

```python
def fetch_source(package: Optional[str], local_path: Optional[str] = None) -> Optional[str]:
    """
    拉取 MCP server 源码。失败返回 None，不抛出异常。
    优先级：local_path > npm pack > 返回 None
    """
    # 本地路径优先
    if local_path and Path(local_path).exists():
        return local_path

    if not package:
        return None

    # 构建缓存目录
    safe_name = package.replace('/', '-').lstrip('@-')
    cache_dir = Path(tempfile.gettempdir()) / "mcp-to-skill-cache" / safe_name

    # 已缓存则直接返回
    if cache_dir.exists() and any(cache_dir.iterdir()):
        return str(cache_dir)

    cache_dir.mkdir(parents=True, exist_ok=True)

    try:
        # npm pack 下载 tarball
        result = subprocess.run(
            ['npm', 'pack', package],
            capture_output=True, text=True, cwd=str(cache_dir), timeout=60
        )
        if result.returncode != 0:
            return None

        tarball = next(cache_dir.glob('*.tgz'), None)
        if not tarball:
            return None

        # 解压（--strip-components=1 去掉 package/ 前缀）
        extract_result = subprocess.run(
            ['tar', 'xzf', str(tarball), '--strip-components=1'],
            capture_output=True, cwd=str(cache_dir), timeout=30
        )
        if extract_result.returncode != 0:
            return None

        return str(cache_dir)
    except Exception:
        return None
```

- [ ] **Step 4: 运行 fetch_source 测试**

```bash
python -m pytest tests/test_mcp_inspector.py -k "fetch_source" -v
```

期望：4 tests PASSED

- [ ] **Step 5: 提交**

```bash
cd /Users/j/Projects/AIAccessories-
git add projects/mcp-to-skill/skills/mcp-to-skill/mcp_inspector.py \
        projects/mcp-to-skill/tests/test_mcp_inspector.py
git commit -m "feat(mcp-to-skill): 实现 fetch_source（npm pack + 本地路径）"
```

---

### Task 3: 实现 connect_and_list_tools（MCP 协议通信）

**Files:**
- Modify: `projects/mcp-to-skill/skills/mcp-to-skill/mcp_inspector.py`
- Modify: `projects/mcp-to-skill/tests/test_mcp_inspector.py`

注意：此函数依赖 `mcp` Python SDK。先验证已安装：

```bash
pip show mcp || pip install mcp
```

- [ ] **Step 1: 写 connect_and_list_tools 失败测试（用 mock）**

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from mcp_inspector import connect_and_list_tools


@pytest.mark.asyncio
async def test_connect_and_list_tools_returns_tool_list():
    """返回格式正确的 tool 列表。"""
    mock_tool = MagicMock()
    mock_tool.name = "search_repos"
    mock_tool.description = "Search GitHub repositories"
    mock_tool.inputSchema = {"type": "object", "properties": {"query": {"type": "string"}}}

    mock_session = AsyncMock()
    mock_session.list_tools.return_value = MagicMock(tools=[mock_tool])

    with patch("mcp_inspector.stdio_client") as mock_ctx, \
         patch("mcp_inspector.ClientSession") as mock_session_cls:
        mock_ctx.return_value.__aenter__ = AsyncMock(return_value=(AsyncMock(), AsyncMock()))
        mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await connect_and_list_tools("npx -y @mcp/server-github")

    assert len(result) == 1
    assert result[0]["name"] == "search_repos"
    assert result[0]["description"] == "Search GitHub repositories"
    assert "inputSchema" in result[0]
    mock_session.initialize.assert_awaited_once()


@pytest.mark.asyncio
async def test_connect_and_list_tools_empty_description():
    """description 为 None 时转为空字符串。"""
    mock_tool = MagicMock()
    mock_tool.name = "tool_no_desc"
    mock_tool.description = None
    mock_tool.inputSchema = {}

    mock_session = AsyncMock()
    mock_session.list_tools.return_value = MagicMock(tools=[mock_tool])

    with patch("mcp_inspector.stdio_client") as mock_ctx, \
         patch("mcp_inspector.ClientSession") as mock_session_cls:
        mock_ctx.return_value.__aenter__ = AsyncMock(return_value=(AsyncMock(), AsyncMock()))
        mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await connect_and_list_tools("npx -y @mcp/server")

    assert result[0]["description"] == ""
```

- [ ] **Step 2: 安装测试依赖**

```bash
pip install pytest pytest-asyncio mcp
```

- [ ] **Step 3: 运行失败测试**

```bash
python -m pytest tests/test_mcp_inspector.py -k "connect_and_list" -v
```

期望：FAILED with `NotImplementedError`

- [ ] **Step 4: 实现 connect_and_list_tools**

在文件顶部添加导入：
```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
```

实现函数：
```python
async def connect_and_list_tools(command: str) -> list[dict]:
    """
    通过 MCP JSON-RPC 协议连接 server，返回 tool 列表。
    command: 完整命令字符串，如 "npx -y @mcp/server-github"
    """
    parts = command.split()
    cmd = parts[0]
    cmd_args = parts[1:]

    params = StdioServerParameters(command=cmd, args=cmd_args)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return [
                {
                    "name": tool.name,
                    "description": tool.description or "",
                    "inputSchema": tool.inputSchema or {}
                }
                for tool in result.tools
            ]
```

- [ ] **Step 5: 运行测试**

```bash
python -m pytest tests/test_mcp_inspector.py -k "connect_and_list" -v
```

期望：2 tests PASSED

- [ ] **Step 6: 提交**

```bash
cd /Users/j/Projects/AIAccessories-
git add projects/mcp-to-skill/skills/mcp-to-skill/mcp_inspector.py \
        projects/mcp-to-skill/tests/test_mcp_inspector.py
git commit -m "feat(mcp-to-skill): 实现 connect_and_list_tools（MCP JSON-RPC 协议）"
```

---

### Task 4: 实现 main() 和 CLI，输出 inspector.json

**Files:**
- Modify: `projects/mcp-to-skill/skills/mcp-to-skill/mcp_inspector.py`
- Modify: `projects/mcp-to-skill/tests/test_mcp_inspector.py`

- [ ] **Step 1: 写 main() 失败测试**

```python
import json
import os
from unittest.mock import patch, AsyncMock, MagicMock
from mcp_inspector import main


def test_main_schema_json_input(tmp_path):
    """--schema-json 模式：直接读取 JSON，跳过 MCP 连接。"""
    tools = [{"name": "t1", "description": "d1", "inputSchema": {}}]
    schema_file = tmp_path / "tools.json"
    schema_file.write_text(json.dumps(tools))
    output_file = tmp_path / "inspector.json"

    with patch("sys.argv", [
        "mcp_inspector.py",
        "--schema-json", str(schema_file),
        "--server-name", "my-server",
        "--output", str(output_file)
    ]):
        main()

    result = json.loads(output_file.read_text())
    assert result["server_name"] == "my-server"
    assert result["package"] is None
    assert result["source_path"] is None
    assert result["tools"] == tools


def test_main_command_input(tmp_path):
    """命令模式：连接 MCP server 并输出 inspector.json。"""
    output_file = tmp_path / "inspector.json"
    mock_tools = [{"name": "search", "description": "Search", "inputSchema": {}}]

    with patch("sys.argv", [
        "mcp_inspector.py",
        "npx -y @mcp/server-github",
        "--output", str(output_file)
    ]), patch("mcp_inspector.connect_and_list_tools", new=AsyncMock(return_value=mock_tools)), \
       patch("mcp_inspector.detect_package", return_value="@mcp/server-github"), \
       patch("mcp_inspector.fetch_source", return_value=None):
        main()

    result = json.loads(output_file.read_text())
    assert result["server_name"] == "server-github"
    assert result["package"] == "@mcp/server-github"
    assert result["tools"] == mock_tools
```

- [ ] **Step 2: 运行失败测试**

```bash
python -m pytest tests/test_mcp_inspector.py -k "test_main" -v
```

期望：FAILED with `NotImplementedError`

- [ ] **Step 3: 实现 main()**

```python
def main():
    parser = argparse.ArgumentParser(
        description="MCP Inspector — 提取 MCP server tool schemas 和源码",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 连接已安装的 MCP server
  python mcp_inspector.py "npx -y @modelcontextprotocol/server-github" --output inspector.json

  # 使用已有 schema JSON（跳过 MCP 连接）
  python mcp_inspector.py --schema-json tools.json --server-name github
        """
    )
    parser.add_argument("command", nargs="?", help="MCP server 启动命令")
    parser.add_argument("--schema-json", help="已有 tool schema JSON 文件路径（跳过 MCP 连接）")
    parser.add_argument("--server-name", help="覆盖 server 名称")
    parser.add_argument("--output", default="inspector.json", help="输出文件路径（默认：inspector.json）")
    args = parser.parse_args()

    # 模式 1：直接使用 schema JSON
    if args.schema_json:
        with open(args.schema_json) as f:
            tools = json.load(f)
        result = {
            "server_name": args.server_name or "unknown",
            "package": None,
            "source_path": None,
            "tools": tools
        }
        _write_output(result, args.output)
        return

    if not args.command:
        parser.error("需要提供 'command' 或 '--schema-json'")

    # 模式 2：连接 MCP server
    tools = asyncio.run(connect_and_list_tools(args.command))
    package = detect_package(args.command)
    source_path = fetch_source(package)

    # 推断 server_name：包名末段 或 命令末段
    if args.server_name:
        server_name = args.server_name
    elif package:
        server_name = package.split("/")[-1]
    else:
        server_name = args.command.split()[-1].split("/")[-1]

    result = {
        "server_name": server_name,
        "package": package,
        "source_path": source_path,
        "tools": tools
    }
    _write_output(result, args.output)


def _write_output(result: dict, output_path: str):
    """写入 inspector.json 并打印摘要。"""
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    tool_count = len(result["tools"])
    src = result["source_path"] or "（无源码）"
    print(f"✓ 写入 {output_path}：{tool_count} 个 tool，源码：{src}")
```

- [ ] **Step 4: 运行全部测试**

```bash
python -m pytest tests/test_mcp_inspector.py -v
```

期望：全部 PASSED

- [ ] **Step 5: 提交**

```bash
cd /Users/j/Projects/AIAccessories-
git add projects/mcp-to-skill/skills/mcp-to-skill/mcp_inspector.py \
        projects/mcp-to-skill/tests/test_mcp_inspector.py
git commit -m "feat(mcp-to-skill): 实现 main() CLI，输出 inspector.json"
```

---

## Chunk 2: SKILL.md

### Task 5: 编写 SKILL.md

**Files:**
- Create: `projects/mcp-to-skill/skills/mcp-to-skill/SKILL.md`

SKILL.md 是 AI 层的完整执行指令，需在零上下文 session 中可独立运行。

- [ ] **Step 1: 创建 SKILL.md**

```markdown
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
```bash
# 将用户粘贴的 JSON 写入临时文件
cat > /tmp/mcp-schema-input.json << 'EOF'
<用户粘贴的 JSON>
EOF
```
进入步骤三时，使用 `--schema-json /tmp/mcp-schema-input.json`。

**C — 用户未指定，想从已注册 MCP 中选择：**
列出当前 agent 已注册的 MCP，让用户选择。
在 Claude Code 中：`claude mcp list`

---

## 步骤二：运行 mcp_inspector.py（仅非 B 类输入：A 或 C）

定位 `mcp_inspector.py`：它与本 SKILL.md 在同一目录。
使用 Bash 工具查找其绝对路径，然后用绝对路径执行：

```bash
# 确认 mcp SDK 已安装
pip show mcp > /dev/null 2>&1 || pip install mcp

# 先用 find 或 ls 确认脚本位置（skill base directory 由框架提供）
# 例：find ~/.claude/skills -name "mcp_inspector.py" 2>/dev/null | head -1
INSPECTOR_PATH="<上一步确认的绝对路径>/mcp_inspector.py"

python "$INSPECTOR_PATH" "<MCP命令>" --output /tmp/mcp-inspector-output.json
```

输出示例：
```
✓ 写入 /tmp/mcp-inspector-output.json：12 个 tool，源码：/tmp/mcp-to-skill-cache/server-github
```

读取输出，获取：`server_name`、`source_path`（可能为 null）、`tools[]`。

---

## 步骤三：AI 分析，推断等价命令

读取 `/tmp/mcp-inspector-output.json`（或步骤一B 的 schema 文件）。

**若 source_path 非 null：**
用 Read / Grep 工具读取源码，定位每个 tool 对应的实现代码，提取：
- HTTP endpoint（URL、method、headers、body 结构）
- 或 CLI 命令调用模式

**若 source_path 为 null：**
仅凭 tool 的 `description` 和 `inputSchema` 推断合理的等价命令。

为每个 tool 写出命令草稿，附置信度标记：
- `[✓ VERIFIED]` — 源码中有明确 API 对应
- `[~ INFERRED]` — AI 推断，逻辑合理但未测试（source_path 为 null 时最高为此级）
- `[! TODO]` — 无法自动生成，留占位说明

---

## 步骤四：测试只读命令

对每个 `[~ INFERRED]` 且为只读操作（GET 请求、查询类）的命令，用 Bash 工具执行测试：

- 测试通过 → 升级为 `[✓ VERIFIED]`
- 测试失败 → 保持 `[~ INFERRED]`，在命令上方注释失败原因
- 写操作（POST/PUT/DELETE、文件修改）**跳过测试**，保持 `[~ INFERRED]`
- `[! TODO]` 项不参与测试

---

## 步骤五：生成 skill 包

**输出目录：** 在用户当前工作目录（或用户指定路径）下创建：
```
<mcp-server-name>/
  SKILL.md
  config.json
  helpers/          （按需，不预先创建）
    tools-extended.md  （tool 数量 > 8 时）
    <tool>.py / <tool>.sh  （逻辑复杂时）
```

**渐进式披露规则：**
- tool 数量 ≤ 8：所有工具写入 SKILL.md
- tool 数量 > 8：SKILL.md 只列最常用 8 个，其余写入 `helpers/tools-extended.md`

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
  "endpoint": "<从源码提取的 base URL，或占位>",
  "auth_token": ""
}
```

注意：config.json 在每次工具调用时读取；若 auth_token 为空，调用需认证的工具前必须提示用户填写，不得使用空 token 继续。

**若 agent 上下文中已加载 skill-creator：**
将分析结果（tool 列表 + 推断命令 + 置信度）传给 skill-creator，由其生成 SKILL.md。

---

## 步骤六：注册 skill 到当前 AI agent

目标：将生成的 skill 目录注册，使其立即可用。按顺序探查：

1. 检测 `npx skills` 是否可用：
```bash
which npx && npx skills --version 2>/dev/null
```
若可用：`npx skills add <skill-path> -g -y`

2. 检测是否为 Claude Code 环境：
```bash
claude --version 2>/dev/null
```
若可用：软链接到 `~/.claude/skills/<skill-name>`（可程序化执行）：
```bash
ln -sf <skill-path> ~/.claude/skills/<skill-name>
```
注意：`/add-dir` 是 Claude Code 的交互式 slash command，不能通过 Bash 调用，提示用户手动操作即可。

3. 均不适用：输出 skill 路径，告知用户：
> "Skill 已生成到 `<path>`，请将该目录注册到你使用的 AI agent。
> Claude Code 用户：运行 `/add-dir <path>`
> npx skills 用户：运行 `npx skills add <path> -g`"

---

## 步骤七：询问是否移除原 MCP（可选）

仅在步骤一为 A/C 类输入（非粘贴 schema）时提示：

> "MCP `<server-name>` 已转换为 skill，是否从你使用的 AI agent 中移除该 MCP 配置？"

- 用户确认 → 协助执行移除操作（agent 自行判断如何移除）
- 用户拒绝或无响应 → 跳过，skill 与 MCP 可并存
```

- [ ] **Step 2: 验证 SKILL.md 格式**

检查：
1. YAML frontmatter 格式正确（`---` 分隔，`name` 和 `description` 字段存在）
2. description 包含触发场景、做什么、不做什么、可选依赖
3. 7 个步骤均有独立的输入分支说明
4. 无硬编码"只能在 Claude Code 使用"类假设

- [ ] **Step 3: 提交**

```bash
cd /Users/j/Projects/AIAccessories-
git add projects/mcp-to-skill/skills/mcp-to-skill/SKILL.md
git commit -m "feat(mcp-to-skill): 添加 SKILL.md（AI 层执行指令）"
```

---

## Chunk 3: 验证与软链接

### Task 6: 集成测试（使用真实 MCP）

**Files:**
- 无新文件，验证现有文件

用一个公开的简单 MCP server 做端到端测试。

- [ ] **Step 1: 验证前置条件**

```bash
# 验证 npx 可用（网络拉取 MCP 必须）
which npx || { echo "npx 不可用，跳过集成测试"; exit 0; }
# 验证 mcp SDK 已安装
pip show mcp > /dev/null || pip install mcp
```

- [ ] **Step 2: 运行 mcp_inspector.py 集成测试**

```bash
cd /Users/j/Projects/AIAccessories-/projects/mcp-to-skill/skills/mcp-to-skill

python mcp_inspector.py "npx -y @modelcontextprotocol/server-filesystem /tmp" \
  --output /tmp/test-inspector.json

cat /tmp/test-inspector.json
```

期望：输出包含 `read_file`、`write_file`、`list_directory` 等 tool，格式为合法 JSON。

- [ ] **Step 3: 检查输出结构**

```bash
python -c "
import json
with open('/tmp/test-inspector.json') as f:
    d = json.load(f)
assert d['server_name']
assert isinstance(d['tools'], list)
assert len(d['tools']) > 0
assert all('name' in t and 'description' in t and 'inputSchema' in t for t in d['tools'])
print(f'OK: {len(d[\"tools\"])} tools, source_path={d[\"source_path\"]}')
"
```

期望：打印 `OK: N tools, source_path=...`

- [ ] **Step 4: 提交（若有修复）**

```bash
cd /Users/j/Projects/AIAccessories-
git add projects/mcp-to-skill/skills/mcp-to-skill/mcp_inspector.py
git commit -m "fix(mcp-to-skill): 集成测试修复" || echo "no changes"
```

---

### Task 7: 软链接到 ~/.claude/skills/

- [ ] **Step 1: 创建软链接**

```bash
SKILL_SRC="$(git -C /Users/j/Projects/AIAccessories- rev-parse --show-toplevel)/projects/mcp-to-skill/skills/mcp-to-skill"
ln -sf "$SKILL_SRC" ~/.claude/skills/mcp-to-skill
```

- [ ] **Step 2: 验证链接**

```bash
ls -la ~/.claude/skills/mcp-to-skill
cat ~/.claude/skills/mcp-to-skill/SKILL.md | head -5
```

期望：显示 SKILL.md 的 frontmatter 开头。

- [ ] **Step 3: 提交软链接说明到 README**

```bash
cd /Users/j/Projects/AIAccessories-/projects/mcp-to-skill
cat > README.md << 'EOF'
# mcp-to-skill

将任意 MCP server 转换为零运行时依赖的 skill 包。

## 安装

```bash
ln -sf $(pwd)/skills/mcp-to-skill ~/.claude/skills/mcp-to-skill
```

## 依赖

```bash
pip install mcp
```

## 使用

在 Claude Code 中触发：
> "把 `npx -y @modelcontextprotocol/server-github` 转成 skill"

详见 [设计文档](docs/2026-03-13-mcp-to-skill-design.md)
EOF

git add README.md
git commit -m "docs(mcp-to-skill): 添加 README 和软链接说明"
```
