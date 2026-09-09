from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / "scripts" / "steel_client_bridge.ps1"
VERIFIER = ROOT / "scripts" / "verify_steel_client.py"


def test_bridge_uses_secret_manager_without_persistent_secret_storage():
    text = BRIDGE.read_text(encoding="utf-8")
    assert "secrets versions access latest" in text
    assert "STEEL_BROWSER_MCP_TOKEN" in text
    assert "SetEnvironmentVariable" not in text
    assert "[EnvironmentVariableTarget]::User" not in text
    assert "Remove-Item Env:STEEL_BROWSER_MCP_TOKEN" in text


def test_bridge_targets_canonical_remote_mcp():
    text = BRIDGE.read_text(encoding="utf-8")
    assert "steel-browser-mcp-518404402696.us-central1.run.app/mcp/" in text
    assert "--bearer-token-env-var STEEL_BROWSER_MCP_TOKEN" in text


def test_verifier_requires_all_five_steel_tools():
    text = VERIFIER.read_text(encoding="utf-8")
    for name in ("create_session", "navigate", "extract", "screenshot", "release_session"):
        assert f'"{name}"' in text
