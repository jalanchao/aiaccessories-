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
