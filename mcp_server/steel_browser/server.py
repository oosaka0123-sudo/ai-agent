"""Steel Cloud Browser MCPServer definition and tool implementations.

Exposes the 5 core tools: create_session, navigate, extract, screenshot, release_session.
"""
from __future__ import annotations

import base64
import logging
import re
from datetime import datetime, timezone
from html import unescape
from typing import Any, Optional

import steel
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from .config import get_steel_config
from .session_manager import SessionTracker
from .url_validator import validate_url_safety

logger = logging.getLogger("mcp_server.steel_browser.server")

mcp = MCPServer(
    name="steel-browser",
    title="Steel Cloud Browser",
    description=(
        "Shared Remote HTTP MCP for Steel Cloud Browser. Provides browser session "
        "management, page navigation, text/markdown extraction, and screenshots."
    ),
)

_steel_client: Any = None
session_tracker = SessionTracker()


def get_steel_client() -> Any:
    global _steel_client
    if _steel_client is None:
        cfg = get_steel_config()
        _steel_client = steel.Steel(steel_api_key=cfg.steel_api_key)
    return _steel_client


def set_steel_client(client: Any) -> None:
    """Helper for injecting a mock Steel client in tests."""
    global _steel_client
    _steel_client = client


def _target_url_or_error(safe_url: Optional[str], last_url: Optional[str]) -> str:
    target_url = safe_url or last_url
    if not target_url:
        raise ToolError(
            "invalid_request: url is required until the session has successfully navigated to an HTTP(S) page."
        )
    try:
        return validate_url_safety(target_url)
    except ValueError as exc:
        raise ToolError(f"invalid_request: {exc}") from exc


def _markdown_to_text(markdown: str) -> str:
    """Convert common Markdown constructs to readable plain text without adding dependencies."""
    text = markdown
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*>\s?", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-+*]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+[.)]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"(`{1,3}|\*\*|__|(?<!\*)\*(?!\*)|(?<!_)_(?!_))", "", text)
    return unescape(text).strip()


@mcp.tool(structured_output=True)
def create_session(
    project_slug: str,
    session_id: Optional[str] = None,
    use_proxy: bool = False,
    solve_captcha: bool = False,
) -> dict[str, Any]:
    """Create a new Steel cloud browser session."""
    if not project_slug or not isinstance(project_slug, str):
        raise ToolError("invalid_request: project_slug is required.")

    client = get_steel_client()
    create_kwargs: dict[str, Any] = {
        "use_proxy": use_proxy,
        "solve_captcha": solve_captcha,
    }
    if session_id:
        create_kwargs["session_id"] = session_id

    try:
        session = client.sessions.create(**create_kwargs)
    except Exception as exc:
        logger.error("Failed to create Steel session: %s", exc)
        raise ToolError(f"steel_api_error: {exc}") from exc

    sid = getattr(session, "id", None) or session_id
    if not sid:
        raise ToolError("steel_api_error: Upstream session creation returned no session ID.")

    debug_url = getattr(session, "session_viewer_url", None) or getattr(session, "debug_url", None)
    info = session_tracker.register(session_id=sid, project_slug=project_slug, debug_url=debug_url)
    created_at_iso = datetime.fromtimestamp(info.created_at, tz=timezone.utc).isoformat()

    return {
        "session_id": sid,
        "status": "active",
        "created_at": created_at_iso,
        "debug_url": debug_url,
        "project_slug": project_slug,
    }


@mcp.tool(structured_output=True)
def navigate(session_id: str, url: str) -> dict[str, Any]:
    """Navigate an existing Steel browser session to a specified URL."""
    if not session_id:
        raise ToolError("invalid_request: session_id is required.")

    try:
        safe_url = validate_url_safety(url)
    except ValueError as exc:
        raise ToolError(f"invalid_request: {exc}") from exc

    info = session_tracker.get(session_id)
    if not info or info.status != "active":
        raise ToolError(f"session_not_found: Session '{session_id}' is not active.")

    client = get_steel_client()
    try:
        scrape_res = client.scrape(url=safe_url, extra_body={"sessionId": session_id})
    except Exception as exc:
        logger.error("Failed to navigate session %s to %s: %s", session_id, safe_url, exc)
        raise ToolError(f"steel_api_error: {exc}") from exc

    session_tracker.touch(session_id, safe_url)
    title = getattr(scrape_res, "title", None) or getattr(scrape_res, "page_title", "")
    return {
        "session_id": session_id,
        "url": safe_url,
        "title": title or f"Page at {safe_url}",
        "status": "success",
    }


@mcp.tool(structured_output=True)
def extract(
    session_id: str,
    url: Optional[str] = None,
    format: str = "markdown",
) -> dict[str, Any]:
    """Extract content (markdown, html, or text) from a Steel session page."""
    if not session_id:
        raise ToolError("invalid_request: session_id is required.")

    info = session_tracker.get(session_id)
    if not info or info.status != "active":
        raise ToolError(f"session_not_found: Session '{session_id}' is not active.")

    safe_url: Optional[str] = None
    if url:
        try:
            safe_url = validate_url_safety(url)
        except ValueError as exc:
            raise ToolError(f"invalid_request: {exc}") from exc

    format_lower = format.lower().strip()
    if format_lower in ("markdown", "md"):
        response_format = "markdown"
        scrape_formats = ["markdown"]
    elif format_lower in ("html", "cleaned_html"):
        response_format = "html"
        scrape_formats = ["html"]
    elif format_lower == "text":
        response_format = "text"
        scrape_formats = ["markdown"]
    else:
        raise ToolError("invalid_request: format must be one of markdown, html, or text.")

    target_url = _target_url_or_error(safe_url, info.last_url)
    client = get_steel_client()
    scrape_kwargs: dict[str, Any] = {
        "extra_body": {"sessionId": session_id},
        "format": scrape_formats,
        "url": target_url,
    }

    try:
        scrape_res = client.scrape(**scrape_kwargs)
    except Exception as exc:
        logger.error("Failed to extract content for session %s: %s", session_id, exc)
        raise ToolError(f"steel_api_error: {exc}") from exc

    session_tracker.touch(session_id, target_url)

    content = ""
    if response_format == "html":
        if hasattr(scrape_res, "html") and scrape_res.html:
            content = scrape_res.html
        elif isinstance(scrape_res, dict):
            content = scrape_res.get("html") or ""
        if not content:
            raise ToolError("steel_api_error: Upstream response contained no HTML content.")
    elif response_format == "text":
        if hasattr(scrape_res, "content") and scrape_res.content:
            content = str(scrape_res.content).strip()
        elif isinstance(scrape_res, dict) and scrape_res.get("content"):
            content = str(scrape_res["content"]).strip()
        else:
            markdown_content = ""
            if hasattr(scrape_res, "markdown") and scrape_res.markdown:
                markdown_content = str(scrape_res.markdown)
            elif isinstance(scrape_res, dict):
                markdown_content = str(scrape_res.get("markdown") or "")
            content = _markdown_to_text(markdown_content)
    else:
        if hasattr(scrape_res, "markdown") and scrape_res.markdown:
            content = scrape_res.markdown
        elif isinstance(scrape_res, dict):
            content = scrape_res.get("markdown") or ""
        if not content:
            raise ToolError("steel_api_error: Upstream response contained no Markdown content.")

    return {
        "session_id": session_id,
        "url": target_url,
        "format": response_format,
        "content": content or "",
    }


@mcp.tool(structured_output=True)
def screenshot(
    session_id: str,
    url: Optional[str] = None,
    full_page: bool = False,
) -> dict[str, Any]:
    """Capture a screenshot of a Steel session page."""
    if not session_id:
        raise ToolError("invalid_request: session_id is required.")

    info = session_tracker.get(session_id)
    if not info or info.status != "active":
        raise ToolError(f"session_not_found: Session '{session_id}' is not active.")

    safe_url: Optional[str] = None
    if url:
        try:
            safe_url = validate_url_safety(url)
        except ValueError as exc:
            raise ToolError(f"invalid_request: {exc}") from exc

    target_url = _target_url_or_error(safe_url, info.last_url)
    client = get_steel_client()
    shot_kwargs: dict[str, Any] = {
        "extra_body": {"sessionId": session_id},
        "full_page": full_page,
        "url": target_url,
    }

    try:
        shot_res = client.screenshot(**shot_kwargs)
    except Exception as exc:
        logger.error("Failed to take screenshot for session %s: %s", session_id, exc)
        raise ToolError(f"steel_api_error: {exc}") from exc

    session_tracker.touch(session_id, target_url)

    b64_data = ""
    if hasattr(shot_res, "image_base64") and shot_res.image_base64:
        b64_data = shot_res.image_base64
    elif hasattr(shot_res, "data") and isinstance(shot_res.data, bytes):
        b64_data = base64.b64encode(shot_res.data).decode("utf-8")
    elif isinstance(shot_res, dict):
        b64_data = shot_res.get("image_base64") or shot_res.get("data") or ""

    return {
        "session_id": session_id,
        "url": target_url,
        "screenshot_base64": b64_data,
        "mime_type": "image/png",
    }


@mcp.tool(structured_output=True)
def release_session(session_id: str) -> dict[str, Any]:
    """Release and close a Steel cloud browser session."""
    if not session_id:
        raise ToolError("invalid_request: session_id is required.")

    client = get_steel_client()
    try:
        client.sessions.release(session_id)
    except Exception as exc:
        logger.warning("Upstream release call for session %s returned: %s", session_id, exc)

    session_tracker.unregister(session_id)
    return {
        "session_id": session_id,
        "status": "released",
    }
