"""Verifies the two MCP tools are actually exposed with the input fields the
integration spec requires, via a real (in-process) MCP protocol round trip —
not by inspecting Python function signatures, so this would catch an SDK
serialization regression too."""
from starlette.testclient import TestClient

from mcp_server.app import create_app

_HEADERS = {"Accept": "application/json, text/event-stream"}


def _list_tools():
    app = create_app()
    with TestClient(app, base_url="http://localhost") as client:
        response = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
            headers=_HEADERS,
        )
    assert response.status_code == 200
    return {tool["name"]: tool for tool in response.json()["result"]["tools"]}


def test_both_tools_are_registered():
    tools = _list_tools()
    assert set(tools) == {"generate_image", "generate_video"}


def test_generate_image_schema_has_required_fields():
    schema = _list_tools()["generate_image"]["inputSchema"]
    for field in ("prompt", "aspect_ratio", "model", "count", "negative_prompt", "output_format", "project_slug"):
        assert field in schema["properties"], field
    assert set(schema["required"]) == {"prompt", "project_slug"}


def test_generate_video_schema_has_required_fields():
    schema = _list_tools()["generate_video"]["inputSchema"]
    for field in ("prompt", "image", "aspect_ratio", "duration_seconds", "model", "negative_prompt", "project_slug"):
        assert field in schema["properties"], field
    assert set(schema["required"]) == {"prompt", "project_slug"}
