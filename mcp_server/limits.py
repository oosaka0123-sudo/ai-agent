"""Billing-accident prevention: hard caps on count, duration, retries, and
concurrency, enforced before any Vertex AI call is made.

`global_max_concurrent` reuses `projects/registry.json`'s existing
`max_parallel_projects` value (already meant, per PR #25, as "the same-time
execution cap, not a cap on how many projects can be registered") instead of
introducing a second, competing knob for the same concept.
"""
from __future__ import annotations

import json
import re
import threading
from pathlib import Path
from typing import Dict

from .config import Limits

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY_PATH = REPO_ROOT / "projects" / "registry.json"

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class LimitError(ValueError):
    """Raised when a request violates a configured safety cap."""


def validate_project_slug(project_slug: str) -> None:
    if not project_slug or not SLUG_RE.fullmatch(project_slug):
        raise LimitError(
            f"invalid project_slug: {project_slug!r} (must be lowercase kebab-case, "
            "matching projects/registry.json's slug format)"
        )


def load_global_max_concurrent(limits: Limits, registry_path: Path = DEFAULT_REGISTRY_PATH) -> int:
    """`GOOGLE_MEDIA_GLOBAL_MAX_CONCURRENT` wins if set (>0); otherwise falls back
    to the registry's `max_parallel_projects`; otherwise a safe default of 4."""
    if limits.global_max_concurrent > 0:
        return limits.global_max_concurrent
    try:
        with registry_path.open("r", encoding="utf-8") as fh:
            registry = json.load(fh)
        value = int(registry.get("max_parallel_projects", 4))
        return value if value > 0 else 4
    except (OSError, ValueError, json.JSONDecodeError):
        return 4


def validate_image_count(count: int, limits: Limits) -> None:
    if count < 1:
        raise LimitError("count must be at least 1")
    if count > limits.max_image_count:
        raise LimitError(f"count={count} exceeds the configured cap of {limits.max_image_count}")


def validate_video_duration(duration_seconds: int | None, limits: Limits) -> None:
    if duration_seconds is None:
        return
    if duration_seconds < 1:
        raise LimitError("duration_seconds must be at least 1")
    if duration_seconds > limits.max_video_duration_seconds:
        raise LimitError(
            f"duration_seconds={duration_seconds} exceeds the configured cap of "
            f"{limits.max_video_duration_seconds}"
        )


class ConcurrencyGate:
    """Enforces both a global concurrency cap and a per-project cap. Thread-safe
    (the MCP server may run tool calls in a threadpool); not asyncio-native by
    design so it works the same whether a given tool handler is sync or async.
    """

    def __init__(self, global_max: int, per_project_max: int) -> None:
        self._global_sema = threading.Semaphore(global_max)
        self._per_project_max = per_project_max
        self._project_counts: Dict[str, int] = {}
        self._lock = threading.Lock()

    def acquire(self, project_slug: str) -> None:
        with self._lock:
            current = self._project_counts.get(project_slug, 0)
            if current >= self._per_project_max:
                raise LimitError(
                    f"project '{project_slug}' already has {current} generation(s) in "
                    f"flight (cap: {self._per_project_max}); try again once one finishes"
                )
            self._project_counts[project_slug] = current + 1
        acquired = self._global_sema.acquire(blocking=False)
        if not acquired:
            with self._lock:
                self._project_counts[project_slug] -= 1
            raise LimitError("global concurrent-generation cap reached; try again shortly")

    def release(self, project_slug: str) -> None:
        with self._lock:
            self._project_counts[project_slug] = max(0, self._project_counts.get(project_slug, 1) - 1)
        self._global_sema.release()
