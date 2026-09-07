"""Google Media MCP tools for image and video generation.

`generate_image` and the legacy `generate_video` keep their existing synchronous
behavior. `start_video_generation` + `check_video_generation` provide a resumable
Veo path for MCP clients whose per-tool timeout is shorter than video generation.
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
    validate_image_uri,
    validate_project_slug,
    validate_video_duration,
)
from .provider_router import ProviderUnavailableError, get_provider, resolve_provider_name
from .storage import GcsUploader, build_gcs_object_path, build_local_scratch_path

mcp = MCPServer(
    name="google-media",
    title="Google Media (Imagen / Veo)",
    description=(
        "Generates images (Gemini) and video (Veo) via Google Vertex AI, "
        "stores results in Google Cloud Storage, and supports resumable video "
        "operations for MCP clients with short request timeouts."
    ),
)

_config: Optional[ServerConfig] = None
_uploader: Optional[GcsUploader] = None
_gate: Optional[ConcurrencyGate] = None


def _lazy_init() -> tuple[ServerConfig, GcsUploader, ConcurrencyGate]:
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


def _persist_assets(
    *,
    generation,
    media_type: str,
    project_slug: str,
    uploader: GcsUploader,
) -> list[dict[str, Any]]:
    scratch_dir = Path(tempfile.mkdtemp(prefix="google-media-"))
    try:
        assets_out = []
        for index, asset in enumerate(generation.assets):
            mime_type = getattr(asset, "mime_type", None)
            local_path = build_local_scratch_path(
                scratch_dir, media_type, mime_type, index=index
            )
            asset.save(str(local_path))
            object_path = build_gcs_object_path(
                project_slug, media_type, local_path.name
            )
            gcs_uri = uploader.upload_file(
                local_path, object_path, content_type=mime_type
            )
            url = uploader.signed_url(object_path)
            assets_out.append({"index": index, "gcs_uri": gcs_uri, "url": url})
        return assets_out
    finally:
        shutil.rmtree(scratch_dir, ignore_errors=True)


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
    validate_project_slug(project_slug)
    try:
        config, uploader, gate = _lazy_init()
    except RuntimeError as exc:
        raise ToolError(f"server_configuration: {exc}") from exc

    try:
        resolved_provider_name = resolve_provider_name(provider_name)
    except ProviderUnavailableError as exc:
        raise ToolError(f"provider_unavailable: {exc}") from exc

    try:
        gate.acquire(project_slug)
    except LimitError as exc:
        raise ToolError(f"rate_limited: {exc}") from exc

    generation_id = uuid.uuid4().hex
    started = time.monotonic()

    try:
        retry_result = run_with_retry(
            call_provider,
            max_attempts=config.limits.max_retry_attempts,
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
        assets_out = _persist_assets(
            generation=generation,
            media_type=media_type,
            project_slug=project_slug,
            uploader=uploader,
        )

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
    """Generate one or more images with Google Vertex AI."""
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
    """Generate a video synchronously. Kept for backward compatibility."""
    try:
        validate_project_slug(project_slug)
        validate_video_duration(duration_seconds, Limits())
        validate_image_uri(image)
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
            image=image,
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


@mcp.tool(structured_output=True)
def start_video_generation(
    prompt: str,
    project_slug: str,
    image: Optional[str] = None,
    aspect_ratio: Optional[str] = None,
    duration_seconds: Optional[int] = None,
    model: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    provider: str = "auto",
) -> dict[str, Any]:
    """Start a Veo job and return immediately with a resumable operation name.

    Use this instead of `generate_video` when the MCP client enforces a short
    per-tool timeout. Call `check_video_generation` with the returned values
    until status becomes `success`.
    """
    try:
        validate_project_slug(project_slug)
        validate_video_duration(duration_seconds, Limits())
        validate_image_uri(image)
    except LimitError as exc:
        raise ToolError(f"invalid_request: {exc}") from exc

    try:
        resolved_provider_name = resolve_provider_name(provider)
        _lazy_init()
        p = get_provider(provider)
        started = p.start_video_generation(
            prompt=prompt,
            model=model,
            count=1,
            aspect_ratio=aspect_ratio,
            negative_prompt=negative_prompt,
            duration_seconds=duration_seconds,
            image=image,
        )
    except ProviderUnavailableError as exc:
        raise ToolError(f"provider_unavailable: {exc}") from exc
    except Exception as exc:
        classified = classify_error(exc)
        raise ToolError(f"{classified.category}: {classified.message}") from exc

    return {
        "provider": resolved_provider_name,
        "type": "video",
        "status": "processing",
        "generation_id": uuid.uuid4().hex,
        "project_slug": project_slug,
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "requested_duration_seconds": duration_seconds,
        "model": started["model"],
        "operation_name": started["operation_name"],
        "image": image,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@mcp.tool(structured_output=True)
def check_video_generation(
    operation_name: str,
    project_slug: str,
    generation_id: str,
    prompt: str,
    model: Optional[str] = None,
    aspect_ratio: Optional[str] = None,
    requested_duration_seconds: Optional[int] = None,
    provider: str = "auto",
) -> dict[str, Any]:
    """Check a resumable Veo job once; upload to GCS only after completion."""
    try:
        validate_project_slug(project_slug)
    except LimitError as exc:
        raise ToolError(f"invalid_request: {exc}") from exc
    if not generation_id:
        raise ToolError("invalid_request: generation_id is required")
    if not operation_name or "/operations/" not in operation_name:
        raise ToolError("invalid_request: valid operation_name is required")

    try:
        resolved_provider_name = resolve_provider_name(provider)
        _, uploader, _ = _lazy_init()
        p = get_provider(provider)
        checked = p.check_video_generation(
            operation_name=operation_name,
            model=model,
        )
    except ProviderUnavailableError as exc:
        raise ToolError(f"provider_unavailable: {exc}") from exc
    except Exception as exc:
        classified = classify_error(exc)
        write_audit_log(
            AuditLogEntry(
                project_slug=project_slug,
                repository=None,
                provider=provider,
                model=model or "(unresolved)",
                type="video",
                prompt=prompt,
                status="failed",
                generation_id=generation_id,
                error=classified.message,
                error_category=classified.category,
                retry_count=0,
                requested_duration_seconds=requested_duration_seconds,
            )
        )
        raise ToolError(f"{classified.category}: {classified.message}") from exc

    if checked["status"] != "success":
        return {
            "provider": resolved_provider_name,
            "type": "video",
            "status": "processing",
            "generation_id": generation_id,
            "project_slug": project_slug,
            "model": checked.get("model") or model,
            "operation_name": operation_name,
        }

    generation = checked["generation"]
    assets_out = _persist_assets(
        generation=generation,
        media_type="video",
        project_slug=project_slug,
        uploader=uploader,
    )
    first = assets_out[0] if assets_out else {}
    created_at = datetime.now(timezone.utc).isoformat()

    write_audit_log(
        AuditLogEntry(
            project_slug=project_slug,
            repository=None,
            provider=resolved_provider_name,
            model=generation.model,
            type="video",
            prompt=prompt,
            status="success",
            generation_id=generation_id,
            output_uri=first.get("gcs_uri"),
            retry_count=0,
            requested_duration_seconds=requested_duration_seconds,
        )
    )

    return {
        "provider": resolved_provider_name,
        "model": generation.model,
        "type": "video",
        "status": "success",
        "generation_id": generation_id,
        "project_slug": project_slug,
        "aspect_ratio": aspect_ratio,
        "requested_duration_seconds": requested_duration_seconds,
        "created_at": created_at,
        "count": len(assets_out),
        "gcs_uri": first.get("gcs_uri"),
        "url": first.get("url"),
        "assets": assets_out,
        "operation_name": operation_name,
    }
