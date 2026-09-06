"""Pytest fixtures for Steel Browser MCP tests.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from mcp_server.steel_browser.server import set_steel_client, session_tracker


@pytest.fixture(autouse=True)
def reset_steel_state(monkeypatch):
    """Ensure clean environment and reset session tracker and mock client before each test."""
    monkeypatch.setenv("STEEL_API_KEY", "mock-steel-api-key")
    monkeypatch.setenv("STEEL_BROWSER_MCP_TOKEN", "test-mcp-bearer-token")
    monkeypatch.setenv("STEEL_BROWSER_MCP_ALLOWED_HOSTS", "testserver,localhost")

    mock_client = MagicMock()
    # Mock session create
    mock_session = MagicMock()
    mock_session.id = "sess_mock_123"
    mock_session.session_viewer_url = "https://steel.dev/debug/sess_mock_123"
    mock_client.sessions.create.return_value = mock_session

    # Mock scrape
    mock_scrape = MagicMock()
    mock_scrape.title = "Example Domain"
    mock_scrape.markdown = "# Example Header\n\nExample content."
    mock_scrape.content = "Example content."
    mock_scrape.html = "<h1>Example Header</h1>"
    mock_scrape.url = "https://example.com"
    mock_client.scrape.return_value = mock_scrape

    # Mock screenshot
    mock_shot = MagicMock()
    mock_shot.image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    mock_shot.url = "https://example.com"
    mock_client.screenshot.return_value = mock_shot

    set_steel_client(mock_client)

    # Clear active sessions in session_tracker
    session_tracker._sessions.clear()

    yield mock_client

    session_tracker._sessions.clear()
    set_steel_client(None)
