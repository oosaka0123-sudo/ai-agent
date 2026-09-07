"""`generate_video`'s `image` argument: a `gs://` URI (the `gcs_uri` a prior
`generate_image` call returned) must reach the provider's `generate_video`
call for real image-to-video conditioning (Issue #43 follow-up) -- it must
no longer be silently dropped.
"""
from __future__ import annotations

import pytest

import mcp_server.server as server_module
from conftest import FakeAsset
from mcp.server.mcpserver.exceptions import ToolError
from media_gen.providers.base import GenerationResult

_VALID_IMAGE_URI = "gs://rss7-ai-media-genmedia/projects/ai-agent/images/2026/09/image_x.png"


class _FakeProvider:
    """Records the kwargs `generate_video` was called with."""

    def __init__(self) -> None:
        self.generate_video_calls: list[dict] = []

    def generate_video(self, **kwargs):
        self.generate_video_calls.append(kwargs)
        return GenerationResult(model="veo-3.1-fast-generate-001", assets=[FakeAsset("video/mp4")])


def test_generate_video_forwards_image_uri_to_provider(inject_fake_backend, monkeypatch):
    inject_fake_backend()
    fake_provider = _FakeProvider()
    monkeypatch.setattr(server_module, "get_provider", lambda _provider: fake_provider)

    result = server_module.generate_video(
        prompt="animate this image",
        project_slug="ai-agent",
        image=_VALID_IMAGE_URI,
    )

    assert result["status"] == "success"
    assert len(fake_provider.generate_video_calls) == 1
    assert fake_provider.generate_video_calls[0]["image"] == _VALID_IMAGE_URI


def test_generate_video_without_image_forwards_none(inject_fake_backend, monkeypatch):
    inject_fake_backend()
    fake_provider = _FakeProvider()
    monkeypatch.setattr(server_module, "get_provider", lambda _provider: fake_provider)

    server_module.generate_video(prompt="text-to-video only", project_slug="ai-agent")

    assert fake_provider.generate_video_calls[0]["image"] is None


@pytest.mark.parametrize(
    "bad_image",
    [
        "not-a-gcs-uri",
        "https://example.com/image.png",
        "/local/path/image.png",
        "gs://",
        "gs://bucket-only",
    ],
)
def test_generate_video_rejects_non_gcs_image(inject_fake_backend, monkeypatch, bad_image):
    inject_fake_backend()
    fake_provider = _FakeProvider()
    monkeypatch.setattr(server_module, "get_provider", lambda _provider: fake_provider)

    with pytest.raises(ToolError, match="invalid_request"):
        server_module.generate_video(
            prompt="animate this image",
            project_slug="ai-agent",
            image=bad_image,
        )

    # must fail before ever reaching the provider
    assert fake_provider.generate_video_calls == []
