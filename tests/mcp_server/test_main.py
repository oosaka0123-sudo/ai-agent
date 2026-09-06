"""Cloud Run runs this container behind a frontend that terminates TLS and
forwards plain HTTP from a non-loopback internal address. Without uvicorn
trusting that address's X-Forwarded-Proto, Starlette's own trailing-slash
redirect (POST /mcp -> /mcp/) is built as an absolute http:// URL, which
strict HTTPS-only clients refuse to follow. This guards against that
regressing silently -- and against that trust widening beyond Cloud Run,
where forwarded headers can't be trusted from just any peer."""
from unittest.mock import patch

from mcp_server.__main__ import main


def test_uvicorn_trusts_forwarded_proto_from_any_peer_on_cloud_run(monkeypatch):
    monkeypatch.delenv("PORT", raising=False)
    monkeypatch.setenv("K_SERVICE", "google-media-mcp")
    with patch("mcp_server.__main__.uvicorn.run") as mock_run:
        main()
    _, kwargs = mock_run.call_args
    assert kwargs["proxy_headers"] is True
    assert kwargs["forwarded_allow_ips"] == "*"


def test_uvicorn_keeps_the_safe_default_off_cloud_run(monkeypatch):
    monkeypatch.delenv("PORT", raising=False)
    monkeypatch.delenv("K_SERVICE", raising=False)
    with patch("mcp_server.__main__.uvicorn.run") as mock_run:
        main()
    _, kwargs = mock_run.call_args
    assert kwargs["proxy_headers"] is True
    assert kwargs["forwarded_allow_ips"] == "127.0.0.1"
