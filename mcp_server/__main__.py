"""Local dev / Cloud Run entrypoint: `python -m mcp_server`.

Cloud Run sets `PORT` and expects the container to listen on `0.0.0.0` on
that port — both handled here rather than baked into the Dockerfile, so the
same image works locally with a different port if needed.
"""
from __future__ import annotations

import os

import uvicorn


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    # Cloud Run terminates TLS at its frontend and forwards plain HTTP to the
    # container from an internal address that isn't 127.0.0.1 (uvicorn's
    # default `forwarded_allow_ips`), so without trusting it here uvicorn
    # never rewrites the ASGI scope's scheme from X-Forwarded-Proto. That
    # leaves Starlette's own trailing-slash redirect (e.g. POST /mcp ->
    # /mcp/) built as an absolute http:// URL, which strict HTTPS-only
    # clients then refuse to follow.
    uvicorn.run(
        "mcp_server.app:app",
        host="0.0.0.0",
        port=port,
        log_config=None,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )


if __name__ == "__main__":
    main()
