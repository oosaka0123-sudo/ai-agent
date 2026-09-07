"""Verify the Google Media MCP tools and their input schemas via MCP."""
from starlette.testclient import TestClient

from mcp_server.app import create_app

_HEADERS = {"Accept": "application/json, text/event-stream"}


def _list_tools(monkeypatch):
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


def test_tools_are_registered(monkeypatch):
    tools = _list_tools(monkeypatch)
    assert set(tools) == {
        "generate_image",
        "generate_video",
        "start_video_generation",
        "check_video_generation",
    }


def test_generate_image_schema_has_required_fields(monkeypatch):
    schema = _list_tools(monkeypatch)["generate_image"]["inputSchema"]
    for field in (
        "prompt",
        "aspect_ratio",
        "model",
        "count",
        "negative_prompt",
        "output_format",
        "project_slug",
    ):
        assert field in schema["properties"], field
    assert set(schema["required"]) == {"prompt", "project_slug"}


def test_generate_video_schema_has_required_fields(monkeypatch):
    schema = _list_tools(monkeypatch)["generate_video"]["inputSchema"]
    for field in (
        "prompt",
        "image",
        "aspect_ratio",
        "duration_seconds",
        "model",
        "negative_prompt",
        "project_slug",
    ):
        assert field in schema["properties"], field
    assert set(schema["required"]) == {"prompt", "project_slug"}


def test_start_video_generation_schema(monkeypatch):
    schema = _list_tools(monkeypatch)["start_video_generation"]["inputSchema"]
    for field in (
        "prompt",
        "project_slug",
        "image",
        "aspect_ratio",
        "duration_seconds",
        "model",
        "negative_prompt",
        "provider",
    ):
        assert field in schema["properties"], field
    assert set(schema["required"]) == {"prompt", "project_slug"}


def test_check_video_generation_schema(monkeypatch):
    schema = _list_tools(monkeypatch)["check_video_generation"]["inputSchema"]
    for field in (
        "operation_name",
        "project_slug",
        "generation_id",
        "prompt",
        "model",
        "aspect_ratio",
        "requested_duration_seconds",
        "provider",
    ):
        assert field in schema["properties"], field
    assert set(schema["required"]) == {
        "operation_name",
        "project_slug",
        "generation_id",
        "prompt",
    }
