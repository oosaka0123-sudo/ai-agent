"""Tests for GitHub OIDC-protected Steel acceptance automation."""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from starlette.testclient import TestClient

import mcp_server.steel_browser.acceptance as acceptance_module
import mcp_server.steel_browser.app as steel_app_module
from mcp_server.steel_app import create_steel_app
from mcp_server.steel_browser.acceptance import (
    run_acceptance_lifecycle,
    verify_github_actions_oidc,
)


def test_acceptance_lifecycle_returns_only_non_secret_evidence(reset_steel_state):
    result = run_acceptance_lifecycle()

    assert result["ok"] is True
    assert result["result"] == "ALL_PASS"
    assert [step["name"] for step in result["steps"]] == [
        "create_session",
        "navigate",
        "extract",
        "screenshot",
        "release_session",
    ]
    assert "session_id" not in str(result)
    assert "screenshot_base64" not in str(result)
    shot = next(step for step in result["steps"] if step["name"] == "screenshot")
    assert shot["base64_chars"] >= 80
    assert shot["mime_type"] == "image/png"


def _github_claims(event_name: str) -> dict[str, object]:
    return {
        "exp": 9999999999,
        "iat": 1,
        "nbf": 1,
        "iss": "https://token.actions.githubusercontent.com",
        "aud": "steel-browser-acceptance",
        "repository": "oosaka0123-sudo/ai-agent",
        "ref": "refs/heads/main",
        "workflow_ref": (
            "oosaka0123-sudo/ai-agent/.github/workflows/"
            "steel-browser-acceptance.yml@refs/heads/main"
        ),
        "event_name": event_name,
    }


def _stub_oidc_crypto(monkeypatch, event_name: str) -> None:
    monkeypatch.setattr(
        acceptance_module._jwks_client,
        "get_signing_key_from_jwt",
        lambda _token: SimpleNamespace(key="public-key"),
    )
    monkeypatch.setattr(
        acceptance_module.jwt,
        "decode",
        lambda *_args, **_kwargs: _github_claims(event_name),
    )


def test_verify_oidc_accepts_push_from_pinned_workflow(monkeypatch):
    _stub_oidc_crypto(monkeypatch, "push")
    assert verify_github_actions_oidc("token")["event_name"] == "push"


def test_verify_oidc_accepts_manual_dispatch(monkeypatch):
    _stub_oidc_crypto(monkeypatch, "workflow_dispatch")
    assert verify_github_actions_oidc("token")["event_name"] == "workflow_dispatch"


def test_verify_oidc_rejects_pull_request_event(monkeypatch):
    _stub_oidc_crypto(monkeypatch, "pull_request")
    with pytest.raises(ValueError, match="event_name"):
        verify_github_actions_oidc("token")


def test_acceptance_endpoint_rejects_missing_oidc(monkeypatch):
    monkeypatch.setenv("STEEL_BROWSER_MCP_TOKEN", "mcp-token")
    with TestClient(create_steel_app(), base_url="http://localhost") as client:
        response = client.post("/acceptance")
    assert response.status_code == 401
    assert response.json() == {"error": "unauthorized"}


def test_acceptance_endpoint_runs_after_oidc_verification(monkeypatch):
    monkeypatch.setenv("STEEL_BROWSER_MCP_TOKEN", "mcp-token")
    monkeypatch.setattr(
        steel_app_module,
        "verify_github_actions_oidc",
        lambda token: {"repository": "oosaka0123-sudo/ai-agent"},
    )
    monkeypatch.setattr(
        steel_app_module,
        "run_acceptance_lifecycle",
        lambda: {
            "ok": True,
            "result": "ALL_PASS",
            "steps": [{"name": "release_session", "status": "pass"}],
        },
    )

    with TestClient(create_steel_app(), base_url="http://localhost") as client:
        response = client.post(
            "/acceptance", headers={"Authorization": "Bearer github-oidc-token"}
        )

    assert response.status_code == 200
    assert response.json()["result"] == "ALL_PASS"


def test_acceptance_endpoint_hides_verification_failure_detail(monkeypatch):
    monkeypatch.setenv("STEEL_BROWSER_MCP_TOKEN", "mcp-token")

    def reject(_token):
        raise ValueError("detailed JWT failure")

    monkeypatch.setattr(steel_app_module, "verify_github_actions_oidc", reject)
    with TestClient(create_steel_app(), base_url="http://localhost") as client:
        response = client.post(
            "/acceptance", headers={"Authorization": "Bearer invalid"}
        )

    assert response.status_code == 401
    assert response.json() == {"error": "unauthorized"}
