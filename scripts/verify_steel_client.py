#!/usr/bin/env python3
"""Verify an authenticated Steel Browser Remote HTTP MCP client connection.

Reads STEEL_BROWSER_MCP_TOKEN only from the process environment and never prints it.
"""

from __future__ import annotations

import asyncio
import os
import sys

from mcp import Client
from mcp.client.streamable_http import httpx2, streamable_http_client

DEFAULT_URL = "https://steel-browser-mcp-518404402696.us-central1.run.app/mcp/"
REQUIRED_TOOLS = {
    "create_session",
    "navigate",
    "extract",
    "screenshot",
    "release_session",
}


async def verify() -> None:
    url = os.environ.get("STEEL_BROWSER_MCP_URL", DEFAULT_URL).strip()
    token = os.environ.get("STEEL_BROWSER_MCP_TOKEN", "").strip()
    if not token:
        raise RuntimeError("STEEL_BROWSER_MCP_TOKEN is not set")

    headers = {"Authorization": f"Bearer {token}"}
    timeout = httpx2.Timeout(20.0, read=60.0)
    async with httpx2.AsyncClient(headers=headers, timeout=timeout) as http_client:
        transport = streamable_http_client(url, http_client=http_client)
        async with Client(transport) as client:
            listed = await client.list_tools()
            names = {tool.name for tool in listed.tools}
            missing = REQUIRED_TOOLS - names
            if missing:
                raise RuntimeError(
                    f"connected, but required tools are missing: {sorted(missing)}"
                )

            print("[PASS] authenticated Steel MCP connection")
            print("[PASS] required tools: " + ", ".join(sorted(REQUIRED_TOOLS)))


def main() -> int:
    try:
        asyncio.run(verify())
    except Exception as exc:  # Keep token and response payloads out of diagnostics.
        print(f"[FAIL] Steel MCP verification: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
