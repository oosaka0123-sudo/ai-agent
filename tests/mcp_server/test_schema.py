"""Verifies the two MCP tools are actually exposed with the input fields the
integration spec requires, via a real (in-process) MCP protocol round trip —
not by inspecting Python function signatures, so this would catch an SDK
serialization regression too."""
from starlette.testclient import TestClient

from mcp_server.app import create_app

_HEADERS = {"Accept": "application/json, text/event-stream"}


def _list_tools(monkeypatch):
    # The MCP endpoint requires bearer auth and a non-empty DNS-rebinding
    # allow-list (both fail closed -- see mcp_server/app.py) since neither
    # is "optional" behavior anymore; this helper only cares about the tool
    # schema, not auth itself, so it just satisfies both like test_auth.py's
    # test_correct_token_is_accepted does.
    monkeypatch.setenv("GOOGLE_MEDIA_MCP_TOKEN", "secret")
    monkeypatch.setenv("GOOGLE_MEDIA_MCP_ALLOWED_HOSTS", "localhost")
    app = create_app()
    with TestClient(app, base_url="http://localhost") as client:
        response = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
            headers={**_HEADERS, "Authorization": "Bearer secret"},
        )
    assert response.status_code == 200
    return {tool["name"]: tool for tool in response.json()["result"]["tools"]}


def test_both_tools_are_registered(monkeypatch):
    tools = _list_tools(monkeypatch)
    assert set(tools) == {"generate_image", "generate_video"}


def test_generate_image_schema_has_required_fields(monkeypatch):
    schema = _list_tools(monkeypatch)["generate_image"]["inputSchema"]
    for field in ("prompt", "aspect_ratio", "model", "count", "negative_prompt", "output_format", "project_slug"):
        assert field in schema["properties"], field
    assert set(schema["required"]) == {"prompt", "project_slug"}


def test_generate_video_schema_has_required_fields(monkeypatch):
    schema = _list_tools(monkeypatch)["generate_video"]["inputSchema"]
    for field in ("prompt", "image", "aspect_ratio", "duration_seconds", "model", "negative_prompt", "project_slug"):
        assert field in schema["properties"], field
    assert set(schema["required"]) == {"prompt", "project_slug"}
