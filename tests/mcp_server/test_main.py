"""Cloud Run runs this container behind a frontend that terminates TLS and
forwards plain HTTP from a non-loopback internal address. Without uvicorn
trusting that address's X-Forwarded-Proto, Starlette's own trailing-slash
redirect (POST /mcp -> /mcp/) is built as an absolute http:// URL, which
strict HTTPS-only clients refuse to follow. This guards against that
regressing silently."""
from unittest.mock import patch

from mcp_server.__main__ import main


def test_uvicorn_trusts_forwarded_proto_from_any_peer(monkeypatch):
    monkeypatch.delenv("PORT", raising=False)
    with patch("mcp_server.__main__.uvicorn.run") as mock_run:
        main()
    _, kwargs = mock_run.call_args
    assert kwargs["proxy_headers"] is True
    assert kwargs["forwarded_allow_ips"] == "*"
