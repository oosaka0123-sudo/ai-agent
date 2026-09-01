"""Shared fixtures for mcp_server tests.

No test in this package makes a real Vertex AI or GCS call: `server.py`
caches its GCP-backed singletons (`_config`, `_uploader`, `_gate`) at module
scope after first use, so tests inject fakes directly into those globals
instead of needing real credentials or network access.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src"
# mcp_server/ is a repo-root package and media_gen/ lives under src/; CI runs
# bare `pytest tests/...` (not `python -m pytest`), which does not add either
# to sys.path itself — same reason every tests/media_gen/*.py file inserts
# src/ manually.
for _p in (REPO_ROOT, SRC_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import mcp_server.server as server_module
from mcp_server.config import Limits, ServerConfig
from mcp_server.limits import ConcurrencyGate


class FakeAsset:
    """Stands in for the google-genai SDK's `types.Image` / `types.Video`."""

    def __init__(self, mime_type: str, content: bytes = b"fake-bytes") -> None:
        self.mime_type = mime_type
        self._content = content
        self.saved_to: list[str] = []

    def save(self, path: str) -> None:
        self.saved_to.append(path)
        Path(path).write_bytes(self._content)


class FakeUploader:
    """Stands in for storage.GcsUploader — records calls, never touches GCS."""

    def __init__(self) -> None:
        self.uploaded: list[tuple[str, str]] = []

    def upload_file(self, local_path: Path, object_path: str, content_type=None) -> str:
        self.uploaded.append((str(local_path), object_path))
        return f"gs://fake-bucket/{object_path}"

    def signed_url(self, object_path: str, expiration_seconds: int = 0):
        return f"https://fake-signed-url/{object_path}"


@pytest.fixture(autouse=True)
def _reset_server_globals(monkeypatch):
    """Every test starts from a clean slate and never leaks a fake config into
    another test (or into a real server process)."""
    monkeypatch.setattr(server_module, "_config", None)
    monkeypatch.setattr(server_module, "_uploader", None)
    monkeypatch.setattr(server_module, "_gate", None)
    yield
    monkeypatch.setattr(server_module, "_config", None)
    monkeypatch.setattr(server_module, "_uploader", None)
    monkeypatch.setattr(server_module, "_gate", None)


@pytest.fixture
def fake_uploader() -> FakeUploader:
    return FakeUploader()


@pytest.fixture
def inject_fake_backend(monkeypatch, fake_uploader: FakeUploader):
    """Pre-populates server.py's lazily-cached globals so `_lazy_init()`
    returns fakes instead of constructing real GCP clients."""

    def _inject(*, limits: Limits | None = None, global_max: int = 4, per_project_max: int = 1):
        config = ServerConfig(
            project="fake-project",
            location="us-central1",
            gcs_bucket="fake-bucket",
            inbound_token="",
            limits=limits or Limits(),
            allowed_hosts=[],
            allowed_origins=[],
        )
        monkeypatch.setattr(server_module, "_config", config)
        monkeypatch.setattr(server_module, "_uploader", fake_uploader)
        monkeypatch.setattr(
            server_module,
            "_gate",
            ConcurrencyGate(global_max=global_max, per_project_max=per_project_max),
        )
        return config

    return _inject
