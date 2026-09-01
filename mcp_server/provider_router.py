"""Provider routing: `provider="google"` today, `provider="auto"` resolves to
whichever provider is actually available, and `provider="higgsfield"` is a
named, not-yet-implemented slot so adding it later is additive (register a
new provider module + one line here), not a restructure.

Every provider module must expose a class with `generate_image(**kwargs)`
and `generate_video(**kwargs)` methods returning
`media_gen.providers.base.GenerationResult` — the same contract
`GoogleVertexProvider` (PR #26) already implements, so the router does not
care which provider it is holding.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Protocol

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from media_gen.providers.base import GenerationResult  # noqa: E402


class MediaProvider(Protocol):
    name: str

    def generate_image(self, **kwargs) -> GenerationResult: ...

    def generate_video(self, **kwargs) -> GenerationResult: ...


class ProviderUnavailableError(RuntimeError):
    pass


# Only "google" is implemented today. Registering "higgsfield" here (once its
# provider module exists, e.g. `mcp_server/providers_higgsfield.py` wrapping
# Kling/Seedance/Flux behind the same GenerationResult contract) is the only
# change needed to light it up — nothing else in this package references
# provider names directly.
_AVAILABLE = ("google",)
_NOT_YET_IMPLEMENTED = ("higgsfield",)


def resolve_provider_name(requested: str) -> str:
    """Turns a possibly-"auto" provider request into a concrete, available
    provider name, or raises ProviderUnavailableError."""
    if requested == "auto":
        if _AVAILABLE:
            return _AVAILABLE[0]
        raise ProviderUnavailableError("no media provider is currently available")
    if requested in _AVAILABLE:
        return requested
    if requested in _NOT_YET_IMPLEMENTED:
        raise ProviderUnavailableError(
            f"provider '{requested}' is planned but not yet implemented; use provider=\"google\" "
            "or provider=\"auto\""
        )
    raise ProviderUnavailableError(f"unknown provider: {requested!r}")


def get_provider(requested: str) -> MediaProvider:
    name = resolve_provider_name(requested)
    if name == "google":
        from media_gen.providers.google_provider import GoogleVertexProvider

        return GoogleVertexProvider()
    raise ProviderUnavailableError(f"unknown provider: {name!r}")  # pragma: no cover - unreachable given _AVAILABLE
