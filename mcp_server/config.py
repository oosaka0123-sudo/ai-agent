"""Environment-driven configuration for the Google Media MCP server.

All values come from environment variables (Cloud Run env vars / Secret
Manager references at deploy time, or a local ``.env`` for development —
never hardcoded, never committed). See ``.env.example`` for the full list.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Limits:
    """Cost-safety caps. All overridable via env vars; defaults are deliberately
    conservative to avoid a runaway-billing accident."""

    max_image_count: int = field(default_factory=lambda: _int_env("GOOGLE_MEDIA_MAX_IMAGE_COUNT", 4))
    max_video_duration_seconds: int = field(
        default_factory=lambda: _int_env("GOOGLE_MEDIA_MAX_VIDEO_DURATION_SECONDS", 8)
    )
    max_retry_attempts: int = field(default_factory=lambda: _int_env("GOOGLE_MEDIA_MAX_RETRY_ATTEMPTS", 2))
    video_poll_interval_seconds: float = field(
        default_factory=lambda: _float_env("GOOGLE_MEDIA_POLL_INTERVAL_SECONDS", 15.0)
    )
    video_timeout_seconds: float = field(
        default_factory=lambda: _float_env("GOOGLE_MEDIA_VIDEO_TIMEOUT_SECONDS", 600.0)
    )
    max_concurrent_per_project: int = field(
        default_factory=lambda: _int_env("GOOGLE_MEDIA_MAX_CONCURRENT_PER_PROJECT", 1)
    )
    # Falls back to registry.json's `max_parallel_projects` (see limits.py) if unset.
    global_max_concurrent: int = field(
        default_factory=lambda: _int_env("GOOGLE_MEDIA_GLOBAL_MAX_CONCURRENT", 0)
    )


def _list_env(name: str) -> list[str]:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class ServerConfig:
    project: str
    location: str
    gcs_bucket: str
    inbound_token: str
    limits: Limits
    allowed_hosts: list[str]
    allowed_origins: list[str]


def get_server_config() -> ServerConfig:
    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "").strip()
    if not project:
        raise RuntimeError(
            "GOOGLE_CLOUD_PROJECT is not set. On Cloud Run this is a required "
            "service env var; locally, set it in .env."
        )
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1").strip() or "us-central1"
    bucket = os.environ.get("GOOGLE_MEDIA_GCS_BUCKET", "").strip()
    if not bucket:
        raise RuntimeError(
            "GOOGLE_MEDIA_GCS_BUCKET is not set. Generated media is never kept on the "
            "server's local filesystem, so a GCS bucket is required."
        )
    # Required so the MCP endpoint itself cannot be called anonymously (Vertex AI
    # calls cost money). This is separate from Cloud Run -> Vertex AI auth, which
    # uses ADC and is not configured here.
    inbound_token = os.environ.get("GOOGLE_MEDIA_MCP_TOKEN", "").strip()

    # The MCP SDK's DNS-rebinding protection defaults to an *empty* allow-list,
    # which rejects every request (not just malicious ones) until the real
    # Cloud Run hostname is registered here. This is a required one-time step
    # after first deploy — see docs/GOOGLE_MEDIA_MCP.md.
    allowed_hosts = _list_env("GOOGLE_MEDIA_MCP_ALLOWED_HOSTS")
    allowed_origins = _list_env("GOOGLE_MEDIA_MCP_ALLOWED_ORIGINS")

    return ServerConfig(
        project=project,
        location=location,
        gcs_bucket=bucket,
        inbound_token=inbound_token,
        limits=Limits(),
        allowed_hosts=allowed_hosts,
        allowed_origins=allowed_origins,
    )
