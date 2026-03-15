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
