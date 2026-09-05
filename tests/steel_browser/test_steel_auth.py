"""Integration tests for Steel Browser MCP authentication and health probes."""
from __future__ import annotations

from starlette.testclient import TestClient

from mcp_server.steel_app import create_steel_app


def test_healthz_unauthenticated(monkeypatch):
    monkeypatch.setenv("STEEL_BROWSER_MCP_TOKEN", "secret-token")
    with TestClient(create_steel_app(), base_url="http://localhost") as client:
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.text == "ok"


def _ready_client(monkeypatch):
    monkeypatch.setenv("STEEL_API_KEY", "key-123")
    monkeypatch.setenv("STEEL_BROWSER_MCP_TOKEN", "token-123")
    monkeypatch.setenv("STEEL_BROWSER_MCP_ALLOWED_HOSTS", "localhost")


def test_readyz_configured(monkeypatch):
    _ready_client(monkeypatch)
    with TestClient(create_steel_app(), base_url="http://localhost") as client:
        response = client.get("/readyz")
        assert response.status_code == 200
        assert response.json() == {"ready": True}


def test_readyz_missing_api_key(monkeypatch):
    _ready_client(monkeypatch)
    monkeypatch.delenv("STEEL_API_KEY", raising=False)
    with TestClient(create_steel_app(), base_url="http://localhost") as client:
        response = client.get("/readyz")
        assert response.status_code == 503
        assert response.json()["ready"] is False


def test_readyz_missing_mcp_token(monkeypatch):
    _ready_client(monkeypatch)
    monkeypatch.delenv("STEEL_BROWSER_MCP_TOKEN", raising=False)
    with TestClient(create_steel_app(), base_url="http://localhost") as client:
        response = client.get("/readyz")
        assert response.status_code == 503
        assert response.json()["ready"] is False


def test_readyz_missing_allowed_hosts(monkeypatch):
    _ready_client(monkeypatch)
    monkeypatch.delenv("STEEL_BROWSER_MCP_ALLOWED_HOSTS", raising=False)
    with TestClient(create_steel_app(), base_url="http://localhost") as client:
        response = client.get("/readyz")
        assert response.status_code == 503
        assert response.json()["ready"] is False
        assert "ALLOWED_HOSTS" in response.json()["error"]


def test_readyz_rejects_zero_ttl(monkeypatch):
    _ready_client(monkeypatch)
    monkeypatch.setenv("STEEL_BROWSER_SESSION_INACTIVITY_TIMEOUT_MINUTES", "0")
    with TestClient(create_steel_app(), base_url="http://localhost") as client:
        response = client.get("/readyz")
        assert response.status_code == 503
        assert response.json()["ready"] is False


def test_readyz_rejects_negative_ttl(monkeypatch):
    _ready_client(monkeypatch)
    monkeypatch.setenv("STEEL_BROWSER_SESSION_MAX_TIMEOUT_MINUTES", "-1")
    with TestClient(create_steel_app(), base_url="http://localhost") as client:
        response = client.get("/readyz")
        assert response.status_code == 503
        assert response.json()["ready"] is False


def test_readyz_rejects_non_integer_ttl(monkeypatch):
    _ready_client(monkeypatch)
    monkeypatch.setenv("STEEL_BROWSER_SESSION_MAX_TIMEOUT_MINUTES", "abc")
    with TestClient(create_steel_app(), base_url="http://localhost") as client:
        response = client.get("/readyz")
        assert response.status_code == 503
        assert response.json()["ready"] is False


def test_readyz_rejects_max_timeout_shorter_than_inactivity(monkeypatch):
    _ready_client(monkeypatch)
    monkeypatch.setenv("STEEL_BROWSER_SESSION_INACTIVITY_TIMEOUT_MINUTES", "20")
    monkeypatch.setenv("STEEL_BROWSER_SESSION_MAX_TIMEOUT_MINUTES", "10")
    with TestClient(create_steel_app(), base_url="http://localhost") as client:
        response = client.get("/readyz")
        assert response.status_code == 503
        assert response.json()["ready"] is False
        assert "greater than or equal" in response.json()["error"]


def test_mcp_auth_middleware_rejects_missing_token(monkeypatch):
    monkeypatch.setenv("STEEL_BROWSER_MCP_TOKEN", "valid-token")
    with TestClient(create_steel_app(), base_url="http://localhost") as client:
        response = client.post("/mcp")
        assert response.status_code == 401
        assert response.json() == {"error": "unauthorized"}


def test_mcp_auth_middleware_rejects_wrong_token(monkeypatch):
    monkeypatch.setenv("STEEL_BROWSER_MCP_TOKEN", "valid-token")
    with TestClient(create_steel_app(), base_url="http://localhost") as client:
        response = client.post("/mcp", headers={"Authorization": "Bearer wrong-token"})
        assert response.status_code == 401
        assert response.json() == {"error": "unauthorized"}


def test_mcp_auth_middleware_accepts_valid_token(monkeypatch):
    monkeypatch.setenv("STEEL_BROWSER_MCP_TOKEN", "valid-token")
    monkeypatch.setenv("STEEL_BROWSER_MCP_ALLOWED_HOSTS", "localhost")
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        },
    }
    headers = {
        "Accept": "application/json, text/event-stream",
        "Authorization": "Bearer valid-token",
    }
    with TestClient(create_steel_app(), base_url="http://localhost") as client:
        response = client.post("/mcp", json=payload, headers=headers)
        assert response.status_code == 200
