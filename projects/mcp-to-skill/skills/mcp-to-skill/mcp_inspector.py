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


async def connect_and_list_tools(command: str) -> list[dict]:
    raise NotImplementedError


def _write_output(result: dict, output_path: str):
    raise NotImplementedError


def main():
    raise NotImplementedError


if __name__ == "__main__":
    main()
