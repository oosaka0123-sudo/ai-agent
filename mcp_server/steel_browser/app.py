"""ASGI Starlette app for Steel Cloud Browser MCP server.

Mounts the MCP server at `/mcp`, adds unauthenticated `/healthz` and `/readyz` probes,
and requires Bearer token authentication (`STEEL_BROWSER_MCP_TOKEN`) on all MCP requests.
"""
from __future__ import annotations

import asyncio
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

from .config import get_steel_config
from .server import get_steel_client, mcp, session_tracker

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
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonLogFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())


class SteelBearerAuthMiddleware(BaseHTTPMiddleware):
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
        get_steel_config()
    except RuntimeError as exc:
        return JSONResponse({"ready": False, "error": str(exc)}, status_code=503)
    return JSONResponse({"ready": True})


async def _session_cleanup_loop(interval_seconds: float = 60.0) -> None:
    while True:
        try:
            await asyncio.sleep(interval_seconds)
            cfg = get_steel_config()
            client = get_steel_client()
            inactivity_sec = cfg.inactivity_timeout_minutes * 60.0
            max_sec = cfg.max_timeout_minutes * 60.0
            session_tracker.cleanup_expired(client, inactivity_sec, max_sec)
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logging.getLogger("mcp_server.steel_browser.app").warning(
                "Error during session cleanup loop: %s", exc
            )


@contextlib.asynccontextmanager
async def _lifespan(_app: Starlette):
    configure_structured_logging()
    cleanup_task = asyncio.create_task(_session_cleanup_loop())
    try:
        async with mcp.session_manager.run():
            yield
    finally:
        cleanup_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await cleanup_task
        try:
            client = get_steel_client()
            session_tracker.release_all(client)
        except Exception:
            pass


def _transport_security() -> TransportSecuritySettings:
    hosts_raw = os.environ.get("STEEL_BROWSER_MCP_ALLOWED_HOSTS", "").strip()
    origins_raw = os.environ.get("STEEL_BROWSER_MCP_ALLOWED_ORIGINS", "").strip()
    allowed_hosts = [h.strip() for h in hosts_raw.split(",") if h.strip()]
    allowed_origins = [o.strip() for o in origins_raw.split(",") if o.strip()]
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=allowed_hosts,
        allowed_origins=allowed_origins,
    )


def create_steel_app() -> Starlette:
    token = os.environ.get("STEEL_BROWSER_MCP_TOKEN", "").strip()
    return Starlette(
        routes=[
            Route("/healthz", _healthz),
            Route("/readyz", _readyz),
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
        middleware=[Middleware(SteelBearerAuthMiddleware, token=token)],
        lifespan=_lifespan,
    )


app = create_steel_app()
