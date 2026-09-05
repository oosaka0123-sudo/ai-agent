"""Entrypoint for Steel Cloud Browser Remote HTTP MCP ASGI application.
"""
from mcp_server.steel_browser.app import app, create_steel_app

__all__ = ["app", "create_steel_app"]
