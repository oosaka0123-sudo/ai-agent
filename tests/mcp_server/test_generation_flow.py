"""Tests for `_run_generation`, the core job -> retry -> upload -> audit-log
orchestration shared by both tools. Every Vertex AI / GCS call is faked
(see conftest.py) — these tests exercise this package's own logic, not the
already-tested-elsewhere (PR #26) provider or the real Google SDK.
"""
import json

import pytest

import mcp_server.server as server_module
from conftest import FakeAsset
from mcp.server.mcpserver.exceptions import ToolError
from media_gen.providers.base import GenerationResult


def test_successful_image_generation_uploads_and_returns_structured_result(inject_fake_backend, fake_uploader, capsys):
    inject_fake_backend()

    def call_provider():
        return GenerationResult(model="imagen-3.0-generate-002", assets=[FakeAsset("image/png")])

    result = server_module._run_generation(
        media_type="image",
        provider_name="google",
        project_slug="rss7-house",
        prompt="a quiet courtyard at blue hour",
        call_provider=call_provider,
        aspect_ratio="16:9",
    )

    assert result["status"] == "success"
    assert result["provider"] == "google"
    assert result["model"] == "imagen-3.0-generate-002"
    assert result["type"] == "image"
    assert result["project_slug"] == "rss7-house"
    assert result["aspect_ratio"] == "16:9"
    assert result["count"] == 1
    assert result["gcs_uri"].startswith("gs://fake-bucket/projects/rss7-house/images/")
    assert result["url"] is not None
    assert result["generation_id"]
    assert result["created_at"]

    # actually uploaded, not just returned in the response
    assert len(fake_uploader.uploaded) == 1

    # audit log line was written to stdout
    log_line = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert log_line["audit"]["status"] == "success"
    assert log_line["audit"]["project_slug"] == "rss7-house"
    assert log_line["audit"]["generation_id"] == result["generation_id"]


def test_multiple_assets_all_uploaded_and_listed(inject_fake_backend, fake_uploader):
    inject_fake_backend()

    def call_provider():
        return GenerationResult(
            model="imagen-3.0-generate-002",
            assets=[FakeAsset("image/png"), FakeAsset("image/png")],
        )

    result = server_module._run_generation(
        media_type="image",
        provider_name="google",
        project_slug="rss7-house",
        prompt="two variations",
        call_provider=call_provider,
        aspect_ratio=None,
    )

    assert result["count"] == 2
    assert len(result["assets"]) == 2
    assert len(fake_uploader.uploaded) == 2


def test_transient_failure_then_success_records_retry_count(inject_fake_backend, capsys):
    inject_fake_backend()
    calls = {"count": 0}

    def call_provider():
        calls["count"] += 1
        if calls["count"] < 2:
            raise RuntimeError("503 temporarily unavailable")
        return GenerationResult(model="imagen-3.0-generate-002", assets=[FakeAsset("image/png")])

    result = server_module._run_generation(
        media_type="image",
        provider_name="google",
        project_slug="rss7-house",
        prompt="retry me",
        call_provider=call_provider,
        aspect_ratio=None,
    )

    assert result["status"] == "success"
    assert calls["count"] == 2  # one failed attempt + one retry, per Limits.max_retry_attempts default (2)


def test_exhausted_retries_raises_tool_error_with_category(inject_fake_backend, capsys):
    inject_fake_backend()

    def call_provider():
        raise RuntimeError("RESOURCE_EXHAUSTED: quota exceeded for this project")

    with pytest.raises(ToolError, match="quota_exceeded"):
        server_module._run_generation(
            media_type="image",
            provider_name="google",
            project_slug="rss7-house",
            prompt="will fail",
            call_provider=call_provider,
            aspect_ratio=None,
        )

    log_line = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert log_line["audit"]["status"] == "failed"
    assert log_line["audit"]["error_category"] == "quota_exceeded"
    assert log_line["audit"]["retry_count"] == 2  # never retries a third time


def test_video_timeout_is_classified_and_does_not_hang(inject_fake_backend):
    inject_fake_backend()

    def call_provider():
        raise TimeoutError("動画生成が600秒以内に完了しませんでした")

    with pytest.raises(ToolError, match="timeout"):
        server_module._run_generation(
            media_type="video",
            provider_name="google",
            project_slug="rss7-house",
            prompt="a slow render",
            call_provider=call_provider,
            aspect_ratio="16:9",
            requested_duration_seconds=8,
        )


def test_never_retries_more_than_configured_cap(inject_fake_backend):
    from mcp_server.config import Limits

    inject_fake_backend(limits=Limits(max_retry_attempts=2))
    calls = {"count": 0}

    def call_provider():
        calls["count"] += 1
        raise RuntimeError("boom")

    with pytest.raises(ToolError):
        server_module._run_generation(
            media_type="image",
            provider_name="google",
            project_slug="rss7-house",
            prompt="always fails",
            call_provider=call_provider,
            aspect_ratio=None,
        )

    assert calls["count"] == 2  # exactly the cap — never unbounded retry


def test_concurrency_released_even_after_failure(inject_fake_backend):
    inject_fake_backend(global_max=1, per_project_max=1)

    def failing_call():
        raise RuntimeError("boom")

    with pytest.raises(ToolError):
        server_module._run_generation(
            media_type="image",
            provider_name="google",
            project_slug="rss7-house",
            prompt="fails",
            call_provider=failing_call,
            aspect_ratio=None,
        )

    # the gate must have been released on failure, or this second call would
    # be wrongly blocked by the first (per-project cap of 1)
    def succeeding_call():
        return GenerationResult(model="m", assets=[FakeAsset("image/png")])

    result = server_module._run_generation(
        media_type="image",
        provider_name="google",
        project_slug="rss7-house",
        prompt="succeeds",
        call_provider=succeeding_call,
        aspect_ratio=None,
    )
    assert result["status"] == "success"
