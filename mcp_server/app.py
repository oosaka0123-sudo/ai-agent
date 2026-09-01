"""ASGI app: mounts the MCP server at exactly `/mcp`, adds an unauthenticated
`/healthz` (Cloud Run startup/liveness probe) and `/readyz` (fails until
config is loadable — catches a missing env var before it becomes a
confusing 500 on the first real tool call), and requires a bearer token
(fail-closed — never optional) on everything else.
"""
from __future__ import annotations

import contextlib
import json
import logging
import os
import sys

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Mount, Route

from mcp.server.transport_security import TransportSecuritySettings

from .config import get_server_config
from .server import mcp

_UNAUTHENTICATED_PATHS = {"/healthz", "/readyz"}


class _JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_structured_logging() -> None:
    """Structured (JSON-per-line) logging to stdout, which Cloud Run's logging
    agent parses natively (`severity` / `message` fields)."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonLogFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Requires `Authorization: Bearer <token>` on every request except the
    health/readiness probes. Fails closed, always: an unset/empty token
    does not disable auth, it just means no request can ever match --
    `config.get_server_config()` requires GOOGLE_MEDIA_MCP_TOKEN for the
    same reason (an empty token must never mean "open"), but that check
    only runs once a tool is actually called; this middleware is what
    protects /mcp itself, on every request, regardless."""

    def __init__(self, app, token: str) -> None:
        super().__init__(app)
        self._token = token

    async def dispatch(self, request: Request, call_next):
        if request.url.path in _UNAUTHENTICATED_PATHS:
            return await call_next(request)
        header = request.headers.get("authorization", "")
        if not self._token or header != f"Bearer {self._token}":
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        return await call_next(request)


async def _healthz(_request: Request) -> PlainTextResponse:
    return PlainTextResponse("ok")


async def _readyz(_request: Request) -> JSONResponse:
    try:
        get_server_config()
    except RuntimeError as exc:
        return JSONResponse({"ready": False, "error": str(exc)}, status_code=503)
    return JSONResponse({"ready": True})


@contextlib.asynccontextmanager
async def _lifespan(_app: Starlette):
    configure_structured_logging()
    async with mcp.session_manager.run():
        yield


def _transport_security() -> TransportSecuritySettings:
    hosts_raw = os.environ.get("GOOGLE_MEDIA_MCP_ALLOWED_HOSTS", "").strip()
    origins_raw = os.environ.get("GOOGLE_MEDIA_MCP_ALLOWED_ORIGINS", "").strip()
    allowed_hosts = [h.strip() for h in hosts_raw.split(",") if h.strip()]
    allowed_origins = [o.strip() for o in origins_raw.split(",") if o.strip()]
    # Always on: an empty allow-list means "reject every request" (the SDK's
    # own default), not "protection off". Silently downgrading protection
    # because the operator forgot to set GOOGLE_MEDIA_MCP_ALLOWED_HOSTS would
    # be exactly the kind of accidental-insecure-deploy this is meant to
    # prevent — see docs/GOOGLE_MEDIA_MCP.md for the required one-time setup
    # step (the server will reject all traffic, loudly, until it's done).
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=allowed_hosts,
        allowed_origins=allowed_origins,
    )


def create_app() -> Starlette:
    token = os.environ.get("GOOGLE_MEDIA_MCP_TOKEN", "").strip()
    return Starlette(
        routes=[
            Route("/healthz", _healthz),
            Route("/readyz", _readyz),
            # Mounted at the exact documented path, not "/" -- the MCP
            # sub-app's own internal routing already restricted it to /mcp
            # either way (its own streamable_http_path default), but mounting
            # narrowly here means that's not the only thing standing between
            # an arbitrary path and the MCP handler.
            Mount(
                "/mcp",
                app=mcp.streamable_http_app(
                    streamable_http_path="/",
                    stateless_http=True,
                    json_response=True,
                    transport_security=_transport_security(),
                ),
            ),
        ],
        middleware=[Middleware(BearerAuthMiddleware, token=token)],
        lifespan=_lifespan,
    )


app = create_app()
