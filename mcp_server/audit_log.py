"""Structured audit logging for every generation request.

Writes one JSON object per line to stdout. On Cloud Run, stdout is captured
by Cloud Logging automatically and durably — the server's local disk is
never the log's home, matching the same "don't rely on local filesystem
persistence" rule as generated media (see storage.py).

Only an explicit allow-list of fields is ever logged. Prompts and error
messages are logged (useful for debugging and Phase 9 requires them), but no
credential, token, or key value is ever accepted into this function's
parameters in the first place, so there is nothing secret to redact.
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class AuditLogEntry:
    project_slug: str
    repository: Optional[str]
    provider: str
    model: str
    type: str
    prompt: str
    status: str  # "success" | "failed"
    generation_id: str
    output_uri: Optional[str] = None
    error: Optional[str] = None
    error_category: Optional[str] = None
    retry_count: int = 0
    requested_duration_seconds: Optional[float] = None
    duration_seconds: Optional[float] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


def write_audit_log(entry: AuditLogEntry, stream=None) -> None:
    # `stream` must be resolved at call time, not as a default argument value
    # (a default is evaluated once, at function-definition time, which would
    # silently bind a stale sys.stdout reference — e.g. from before a test
    # framework or logging setup replaces it).
    if stream is None:
        stream = sys.stdout
    print(json.dumps({"audit": entry.to_dict()}, ensure_ascii=False), file=stream, flush=True)
