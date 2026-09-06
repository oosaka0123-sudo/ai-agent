"""Unit tests for the 5 Steel Cloud Browser MCP tools:
create_session, navigate, extract, screenshot, release_session.
"""
from __future__ import annotations

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from mcp_server.steel_browser.server import (
    create_session,
    extract,
    navigate,
    release_session,
    screenshot,
    session_tracker,
)


def test_create_session(reset_steel_state):
    mock_client = reset_steel_state
    result = create_session(project_slug="my-project")
    assert result["session_id"] == "sess_mock_123"
    assert result["status"] == "active"
    assert result["project_slug"] == "my-project"
    assert "debug_url" in result
    assert mock_client.sessions.create.called


def test_create_session_missing_project_slug():
    with pytest.raises(ToolError, match="project_slug is required"):
        create_session(project_slug="")


def test_navigate_success(reset_steel_state):
    mock_client = reset_steel_state
    create_session(project_slug="my-project")
    nav_res = navigate(session_id="sess_mock_123", url="https://example.com")
    assert nav_res["session_id"] == "sess_mock_123"
    assert nav_res["url"] == "https://example.com"
    assert nav_res["status"] == "success"
    assert mock_client.scrape.called


def test_navigate_ssrf_blocked():
    create_session(project_slug="my-project")
    with pytest.raises(ToolError, match="SSRF protection"):
        navigate(session_id="sess_mock_123", url="http://127.0.0.1:8080")


def test_navigate_nonexistent_session():
    with pytest.raises(ToolError, match="session_not_found"):
        navigate(session_id="invalid_id", url="https://example.com")


def test_extract_markdown(reset_steel_state):
    create_session(project_slug="my-project")
    ext_res = extract(session_id="sess_mock_123", url="https://example.com", format="markdown")
    assert ext_res["session_id"] == "sess_mock_123"
    assert ext_res["format"] == "markdown"
    assert "Example Header" in ext_res["content"]


def test_extract_html(reset_steel_state):
    create_session(project_slug="my-project")
    ext_res = extract(session_id="sess_mock_123", url="https://example.com", format="html")
    assert ext_res["format"] == "html"
    assert "<h1>Example Header</h1>" in ext_res["content"]


def test_extract_text_prefers_plain_content(reset_steel_state):
    create_session(project_slug="my-project")
    ext_res = extract(session_id="sess_mock_123", url="https://example.com", format="text")
    assert ext_res["format"] == "text"
    assert ext_res["content"] == "Example content."
    assert "#" not in ext_res["content"]


def test_extract_text_strips_markdown_when_plain_content_missing(reset_steel_state):
    mock_client = reset_steel_state
    mock_client.scrape.return_value.content = ""
    create_session(project_slug="my-project")
    ext_res = extract(session_id="sess_mock_123", url="https://example.com", format="text")
    assert ext_res["content"] == "Example Header\n\nExample content."
    assert "#" not in ext_res["content"]


def test_extract_without_url_before_navigation_rejected(reset_steel_state):
    create_session(project_slug="my-project")
    with pytest.raises(ToolError, match="url is required"):
        extract(session_id="sess_mock_123")


def test_screenshot_without_url_before_navigation_rejected(reset_steel_state):
    create_session(project_slug="my-project")
    with pytest.raises(ToolError, match="url is required"):
        screenshot(session_id="sess_mock_123")


def test_navigate_then_extract_without_url_uses_last_url(reset_steel_state):
    create_session(project_slug="my-project")
    navigate(session_id="sess_mock_123", url="https://example.com/target-page")
    ext_res = extract(session_id="sess_mock_123")
    assert ext_res["url"] == "https://example.com/target-page"


def test_screenshot_success(reset_steel_state):
    create_session(project_slug="my-project")
    shot_res = screenshot(session_id="sess_mock_123", url="https://example.com", full_page=True)
    assert shot_res["session_id"] == "sess_mock_123"
    assert shot_res["url"] == "https://example.com"
    assert shot_res["mime_type"] == "image/png"
    assert len(shot_res["screenshot_base64"]) > 0


def test_screenshot_after_navigation_returns_last_url(reset_steel_state):
    create_session(project_slug="my-project")
    navigate(session_id="sess_mock_123", url="https://example.com/target-page")
    shot_res = screenshot(session_id="sess_mock_123")
    assert shot_res["url"] == "https://example.com/target-page"


def test_release_session(reset_steel_state):
    mock_client = reset_steel_state
    create_session(project_slug="my-project")
    rel_res = release_session(session_id="sess_mock_123")
    assert rel_res["status"] == "released"
    assert session_tracker.get("sess_mock_123") is None
    mock_client.sessions.release.assert_called_with("sess_mock_123")
