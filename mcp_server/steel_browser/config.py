"""Environment-driven configuration for the Steel Cloud Browser MCP server.

All values come from environment variables. Secret keys (STEEL_API_KEY)
and inbound tokens (STEEL_BROWSER_MCP_TOKEN) are read from environment
and never logged or committed.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


def _positive_int_env(name: str, default: int) -> int:
    """Read a positive integer env var and fail closed on invalid values."""
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a positive integer.") from exc
    if value <= 0:
        raise RuntimeError(f"{name} must be greater than 0.")
    return value


def _list_env(name: str) -> list[str]:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class SteelServerConfig:
    steel_api_key: str
    inbound_token: str
    allowed_hosts: list[str]
    allowed_origins: list[str]
    inactivity_timeout_minutes: int
    max_timeout_minutes: int


def get_steel_config() -> SteelServerConfig:
    api_key = os.environ.get("STEEL_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "STEEL_API_KEY is not set. This is required to communicate with Steel Cloud Browser."
        )

    inbound_token = os.environ.get("STEEL_BROWSER_MCP_TOKEN", "").strip()
    if not inbound_token:
        raise RuntimeError(
            "STEEL_BROWSER_MCP_TOKEN is not set. This inbound token protects the MCP endpoint from unauthenticated access."
        )

    allowed_hosts = _list_env("STEEL_BROWSER_MCP_ALLOWED_HOSTS")
    if not allowed_hosts:
        raise RuntimeError(
            "STEEL_BROWSER_MCP_ALLOWED_HOSTS is not set. At least one explicit host is required for DNS rebinding protection."
        )
    allowed_origins = _list_env("STEEL_BROWSER_MCP_ALLOWED_ORIGINS")

    inactivity_timeout = _positive_int_env(
        "STEEL_BROWSER_SESSION_INACTIVITY_TIMEOUT_MINUTES", 10
    )
    max_timeout = _positive_int_env("STEEL_BROWSER_SESSION_MAX_TIMEOUT_MINUTES", 30)
    if max_timeout < inactivity_timeout:
        raise RuntimeError(
            "STEEL_BROWSER_SESSION_MAX_TIMEOUT_MINUTES must be greater than or equal to STEEL_BROWSER_SESSION_INACTIVITY_TIMEOUT_MINUTES."
        )

    return SteelServerConfig(
        steel_api_key=api_key,
        inbound_token=inbound_token,
        allowed_hosts=allowed_hosts,
        allowed_origins=allowed_origins,
        inactivity_timeout_minutes=inactivity_timeout,
        max_timeout_minutes=max_timeout,
    )
