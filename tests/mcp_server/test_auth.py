"""Inbound bearer-token auth on the MCP endpoint itself (separate from
Cloud Run -> Vertex AI auth, which uses ADC and isn't exercised here)."""
import os

from starlette.testclient import TestClient

from mcp_server.app import create_app

_HEADERS = {"Accept": "application/json, text/event-stream"}
_TOOLS_LIST = {"jsonrpc": "2.0", "method": "tools/list", "id": 1}


def test_health_and_ready_never_require_auth(monkeypatch):
    monkeypatch.setenv("GOOGLE_MEDIA_MCP_TOKEN", "secret")
    app = create_app()
    with TestClient(app, base_url="http://localhost") as client:
        assert client.get("/healthz").status_code == 200
        # readyz may 503 (no GCP env in tests) but must not 401
        assert client.get("/readyz").status_code != 401


def test_missing_authentication_is_rejected(monkeypatch):
    monkeypatch.setenv("GOOGLE_MEDIA_MCP_TOKEN", "secret")
    app = create_app()
    with TestClient(app, base_url="http://localhost") as client:
        response = client.post("/mcp", json=_TOOLS_LIST, headers=_HEADERS)
    assert response.status_code == 401


def test_wrong_token_is_rejected(monkeypatch):
    monkeypatch.setenv("GOOGLE_MEDIA_MCP_TOKEN", "secret")
    app = create_app()
    with TestClient(app, base_url="http://localhost") as client:
        response = client.post(
            "/mcp", json=_TOOLS_LIST, headers={**_HEADERS, "Authorization": "Bearer wrong"}
        )
    assert response.status_code == 401


def test_correct_token_is_accepted(monkeypatch):
    monkeypatch.setenv("GOOGLE_MEDIA_MCP_TOKEN", "secret")
    monkeypatch.setenv("GOOGLE_MEDIA_MCP_ALLOWED_HOSTS", "localhost")
    app = create_app()
    with TestClient(app, base_url="http://localhost") as client:
        response = client.post(
            "/mcp", json=_TOOLS_LIST, headers={**_HEADERS, "Authorization": "Bearer secret"}
        )
    assert response.status_code == 200
