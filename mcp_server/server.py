"""The two MCP tools: `generate_image` and `generate_video`.

Both tools run the full job → poll → success/failed → save-to-GCS cycle
inside the tool call itself, so Claude Code makes one call and gets a final
result — it never has to poll. All Vertex AI calls go through
`media_gen.providers.google_provider.GoogleVertexProvider` (PR #26); this
module only adds request validation, provider routing, retry orchestration,
GCS persistence, audit logging, and cost-safety limits around it.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from media_gen.retry import run_with_retry  # noqa: E402

from .audit_log import AuditLogEntry, write_audit_log
from .config import Limits, ServerConfig, get_server_config
from .errors import classify_error
from .limits import (
    ConcurrencyGate,
    LimitError,
    load_global_max_concurrent,
    validate_image_count,
    validate_project_slug,
    validate_video_duration,
)
from .provider_router import ProviderUnavailableError, get_provider, resolve_provider_name
from .storage import GcsUploader, build_gcs_object_path, build_local_scratch_path

mcp = MCPServer(
    name="google-media",
    title="Google Media (Imagen / Veo)",
    description=(
        "Generates images (Imagen) and video (Veo) via Google Vertex AI, "
        "stores the results in Google Cloud Storage, and returns their "
        "location. Video generation is handled fully server-side, "
        "including polling — a single call returns the final result."
    ),
)

_config: Optional[ServerConfig] = None
_uploader: Optional[GcsUploader] = None
_gate: Optional[ConcurrencyGate] = None


def _lazy_init() -> tuple[ServerConfig, GcsUploader, ConcurrencyGate]:
    """Deferred so importing this module (e.g. for tests) never requires real
    GCP env vars or credentials unless a tool is actually invoked."""
    global _config, _uploader, _gate
    if _config is None:
        _config = get_server_config()
        _uploader = GcsUploader(_config.gcs_bucket)
        _gate = ConcurrencyGate(
            global_max=load_global_max_concurrent(_config.limits),
            per_project_max=_config.limits.max_concurrent_per_project,
        )
    assert _uploader is not None and _gate is not None
    return _config, _uploader, _gate


def _run_generation(
    *,
    media_type: str,
    provider_name: str,
    project_slug: str,
    prompt: str,
    call_provider,
    aspect_ratio: Optional[str],
    requested_duration_seconds: Optional[float] = None,
) -> dict[str, Any]:
    # Validate before touching GCP config, so a malformed request fails with a
    # clear message even if the server's own GOOGLE_CLOUD_PROJECT/GCS bucket
    # env vars happen to be missing or misconfigured.
    validate_project_slug(project_slug)
    try:
        config, uploader, gate = _lazy_init()
    except RuntimeError as exc:
        raise ToolError(f"server_configuration: {exc}") from exc

    try:
        # Only resolves the *name* here (cheap) — the actual provider client
        # is constructed once, lazily, inside `call_provider` itself. Doing
        # it here too would construct (e.g.) GoogleVertexProvider twice per
        # request for no reason, and its own RuntimeError (missing GCP env
        # vars) wouldn't be one this except clause catches anyway.
        resolved_provider_name = resolve_provider_name(provider_name)
    except ProviderUnavailableError as exc:
        raise ToolError(f"provider_unavailable: {exc}") from exc

    try:
        gate.acquire(project_slug)
    except LimitError as exc:
        raise ToolError(f"rate_limited: {exc}") from exc

    generation_id = uuid.uuid4().hex
    started = time.monotonic()
    retry_count = 0

    def on_attempt_failed(attempt: int, exc: Exception) -> None:
        nonlocal retry_count
        retry_count = attempt

    try:
        retry_result = run_with_retry(
            call_provider,
            max_attempts=config.limits.max_retry_attempts,
            on_attempt_failed=on_attempt_failed,
        )

        if not retry_result.success:
            classified = classify_error(retry_result.error)
            write_audit_log(
                AuditLogEntry(
                    project_slug=project_slug,
                    repository=None,
                    provider=resolved_provider_name,
                    model="(unresolved)",
                    type=media_type,
                    prompt=prompt,
                    status="failed",
                    generation_id=generation_id,
                    error=classified.message,
                    error_category=classified.category,
                    retry_count=retry_result.attempts,
                    requested_duration_seconds=requested_duration_seconds,
                    duration_seconds=time.monotonic() - started,
                )
            )
            raise ToolError(f"{classified.category}: {classified.message}")

        generation = retry_result.value
        scratch_dir = Path(tempfile.mkdtemp(prefix="google-media-"))
        try:
            assets_out = []
            for index, asset in enumerate(generation.assets):
                mime_type = getattr(asset, "mime_type", None)
                local_path = build_local_scratch_path(scratch_dir, media_type, mime_type, index=index)
                asset.save(str(local_path))
                object_path = build_gcs_object_path(project_slug, media_type, local_path.name)
                gcs_uri = uploader.upload_file(local_path, object_path, content_type=mime_type)
                url = uploader.signed_url(object_path)
                assets_out.append({"index": index, "gcs_uri": gcs_uri, "url": url})
        finally:
            shutil.rmtree(scratch_dir, ignore_errors=True)

        duration_seconds = time.monotonic() - started
        created_at = datetime.now(timezone.utc).isoformat()

        write_audit_log(
            AuditLogEntry(
                project_slug=project_slug,
                repository=None,
                provider=resolved_provider_name,
                model=generation.model,
                type=media_type,
                prompt=prompt,
                status="success",
                generation_id=generation_id,
                output_uri=assets_out[0]["gcs_uri"] if assets_out else None,
                retry_count=retry_result.attempts,
                requested_duration_seconds=requested_duration_seconds,
                duration_seconds=duration_seconds,
            )
        )

        first = assets_out[0] if assets_out else {}
        return {
            "provider": resolved_provider_name,
            "model": generation.model,
            "type": media_type,
            "status": "success",
            "generation_id": generation_id,
            "project_slug": project_slug,
            "aspect_ratio": aspect_ratio,
            "requested_duration_seconds": requested_duration_seconds,
            "created_at": created_at,
            "processing_seconds": round(duration_seconds, 2),
            "count": len(assets_out),
            "gcs_uri": first.get("gcs_uri"),
            "url": first.get("url"),
            "assets": assets_out,
        }
    finally:
        gate.release(project_slug)


@mcp.tool(structured_output=True)
def generate_image(
    prompt: str,
    project_slug: str,
    aspect_ratio: Optional[str] = None,
    model: Optional[str] = None,
    count: int = 1,
    negative_prompt: Optional[str] = None,
    output_format: str = "image/png",
    provider: str = "auto",
) -> dict[str, Any]:
    """Generate one or more images with Google Vertex AI (Imagen).

    Args:
        prompt: What to generate.
        project_slug: The registered site/project this belongs to (lowercase
            kebab-case, matching projects/registry.json). Used for GCS
            layout and audit logs — required so generated media always has
            a clear owner.
        aspect_ratio: e.g. "1:1", "16:9", "9:16". Provider default if omitted.
        model: Overrides the provider's default image model.
        count: Number of images (capped by GOOGLE_MEDIA_MAX_IMAGE_COUNT).
        negative_prompt: Elements to avoid.
        output_format: Image MIME type, e.g. "image/png".
        provider: "google" (only implemented provider today) or "auto".
    """
    # Cheap, GCP-config-independent validation first (see _run_generation).
    try:
        validate_project_slug(project_slug)
        validate_image_count(count, Limits())
    except LimitError as exc:
        raise ToolError(f"invalid_request: {exc}") from exc

    def call_provider():
        p = get_provider(provider)
        return p.generate_image(
            prompt=prompt,
            model=model,
            count=count,
            aspect_ratio=aspect_ratio,
            negative_prompt=negative_prompt,
            output_mime_type=output_format,
        )

    return _run_generation(
        media_type="image",
        provider_name=provider,
        project_slug=project_slug,
        prompt=prompt,
        call_provider=call_provider,
        aspect_ratio=aspect_ratio,
    )


@mcp.tool(structured_output=True)
def generate_video(
    prompt: str,
    project_slug: str,
    image: Optional[str] = None,
    aspect_ratio: Optional[str] = None,
    duration_seconds: Optional[int] = None,
    model: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    provider: str = "auto",
) -> dict[str, Any]:
    """Generate a video with Google Vertex AI (Veo). Fully synchronous from
    the caller's point of view: this call starts the job, polls until it
    finishes or times out, uploads the result to GCS, and returns the final
    outcome — never a job ID to poll separately.

    Args:
        prompt: What to generate.
        project_slug: The registered site/project this belongs to (lowercase
            kebab-case, matching projects/registry.json).
        image: Reserved for image-to-video conditioning once the provider
            wrapper supports it; currently ignored if passed.
        aspect_ratio: e.g. "16:9", "9:16".
        duration_seconds: Clip length (capped by
            GOOGLE_MEDIA_MAX_VIDEO_DURATION_SECONDS).
        model: Overrides the provider's default video model.
        negative_prompt: Elements to avoid.
        provider: "google" (only implemented provider today) or "auto".
    """
    # Cheap, GCP-config-independent validation first (see _run_generation).
    try:
        validate_project_slug(project_slug)
        validate_video_duration(duration_seconds, Limits())
    except LimitError as exc:
        raise ToolError(f"invalid_request: {exc}") from exc

    def call_provider():
        config, _, _ = _lazy_init()
        p = get_provider(provider)
        return p.generate_video(
            prompt=prompt,
            model=model,
            count=1,
            aspect_ratio=aspect_ratio,
            negative_prompt=negative_prompt,
            duration_seconds=duration_seconds,
            poll_interval=config.limits.video_poll_interval_seconds,
            timeout=config.limits.video_timeout_seconds,
        )

    return _run_generation(
        media_type="video",
        provider_name=provider,
        project_slug=project_slug,
        prompt=prompt,
        call_provider=call_provider,
        aspect_ratio=aspect_ratio,
        requested_duration_seconds=duration_seconds,
    )
