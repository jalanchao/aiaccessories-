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
