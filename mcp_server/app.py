"""ASGI app: mounts the MCP server under `/mcp`, adds an unauthenticated
`/healthz` (Cloud Run startup/liveness probe) and `/readyz` (fails until
config is loadable — catches a missing env var before it becomes a
confusing 500 on the first real tool call), and requires a bearer token on
everything else.
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
    health/readiness probes. If GOOGLE_MEDIA_MCP_TOKEN is unset, auth is
    disabled — intentional for local development, but get_server_config()
    already fails closed on Cloud Run if the operator forgets to set the
    other required env vars, and README/docs call out that leaving this
    unset in a deployed environment means the endpoint is open."""

    def __init__(self, app, token: str) -> None:
        super().__init__(app)
        self._token = token

    async def dispatch(self, request: Request, call_next):
        if not self._token or request.url.path in _UNAUTHENTICATED_PATHS:
            return await call_next(request)
        header = request.headers.get("authorization", "")
        if header != f"Bearer {self._token}":
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
    # The SDK's default (empty allow-list, protection on) rejects *every*
    # request, not just malicious ones, until the real Cloud Run hostname is
    # registered — see docs/GOOGLE_MEDIA_MCP.md for the one-time setup step.
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=bool(allowed_hosts),
        allowed_hosts=allowed_hosts,
        allowed_origins=allowed_origins,
    )


def create_app() -> Starlette:
    token = os.environ.get("GOOGLE_MEDIA_MCP_TOKEN", "").strip()
    return Starlette(
        routes=[
            Route("/healthz", _healthz),
            Route("/readyz", _readyz),
            Mount(
                "/",
                app=mcp.streamable_http_app(
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
