"""GoogleVertexProvider: generate_image は Gemini の generate_content
(response_modalities=["IMAGE"]) を、generate_video は Veo の generate_videos
を呼び出す。実際のVertex AI呼び出しは行わず、genai.Client をモックする。"""
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from google.genai import types

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from media_gen.providers import google_provider  # noqa: E402
from media_gen.providers.google_provider import GoogleVertexProvider  # noqa: E402


@pytest.fixture(autouse=True)
def _google_env(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "fake-project")
    monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "us-central1")


def _make_client_with_image_response(image_bytes: bytes = b"fake-png-bytes", mime_type: str = "image/png"):
    fake_client = MagicMock()
    part = types.Part(inline_data=types.Blob(data=image_bytes, mime_type=mime_type))
    candidate = types.Candidate(content=types.Content(parts=[part]))
    fake_client.models.generate_content.return_value = types.GenerateContentResponse(candidates=[candidate])
    return fake_client


def test_generate_image_uses_gemini_generate_content(monkeypatch):
    fake_client = _make_client_with_image_response()
    monkeypatch.setattr(google_provider.genai, "Client", lambda **_: fake_client)

    provider = GoogleVertexProvider()
    result = provider.generate_image(prompt="a blue circle")

    fake_client.models.generate_content.assert_called_once()
    call_kwargs = fake_client.models.generate_content.call_args.kwargs
    assert call_kwargs["model"] == google_provider.DEFAULT_IMAGE_MODEL
    assert call_kwargs["contents"] == "a blue circle"
    assert call_kwargs["config"].response_modalities == ["IMAGE"]

    assert result.model == google_provider.DEFAULT_IMAGE_MODEL
    assert len(result.assets) == 1
    asset = result.assets[0]
    assert asset.image_bytes == b"fake-png-bytes"
    assert asset.mime_type == "image/png"


def test_generate_image_respects_model_override(monkeypatch):
    fake_client = _make_client_with_image_response()
    monkeypatch.setattr(google_provider.genai, "Client", lambda **_: fake_client)

    provider = GoogleVertexProvider()
    result = provider.generate_image(prompt="a blue circle", model="gemini-2.5-pro-image")

    assert result.model == "gemini-2.5-pro-image"
    assert fake_client.models.generate_content.call_args.kwargs["model"] == "gemini-2.5-pro-image"


def test_generate_image_folds_negative_prompt_into_contents(monkeypatch):
    fake_client = _make_client_with_image_response()
    monkeypatch.setattr(google_provider.genai, "Client", lambda **_: fake_client)

    provider = GoogleVertexProvider()
    provider.generate_image(prompt="a cat", negative_prompt="no dogs")

    contents = fake_client.models.generate_content.call_args.kwargs["contents"]
    assert "a cat" in contents
    assert "no dogs" in contents


def test_generate_image_raises_when_no_images_returned(monkeypatch):
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = types.GenerateContentResponse(candidates=[])
    monkeypatch.setattr(google_provider.genai, "Client", lambda **_: fake_client)

    provider = GoogleVertexProvider()
    with pytest.raises(RuntimeError):
        provider.generate_image(prompt="a blue circle")


def test_default_video_model_is_veo_3_1_lite():
    assert google_provider.DEFAULT_VIDEO_MODEL == "veo-3.1-lite-generate-001"


def test_generate_video_uses_default_model(monkeypatch):
    fake_client = MagicMock()
    operation = MagicMock()
    operation.done = True
    operation.error = None
    video = MagicMock()
    operation.result.generated_videos = [MagicMock(video=video)]
    fake_client.models.generate_videos.return_value = operation
    monkeypatch.setattr(google_provider.genai, "Client", lambda **_: fake_client)

    provider = GoogleVertexProvider()
    result = provider.generate_video(prompt="a cat walking")

    call_kwargs = fake_client.models.generate_videos.call_args.kwargs
    assert call_kwargs["model"] == "veo-3.1-lite-generate-001"
    assert call_kwargs["source"].image is None
    assert result.model == "veo-3.1-lite-generate-001"
    assert result.assets == [video]


def test_generate_video_respects_fast_model_override(monkeypatch):
    fake_client = MagicMock()
    operation = MagicMock()
    operation.done = True
    operation.error = None
    operation.result.generated_videos = [MagicMock(video=MagicMock())]
    fake_client.models.generate_videos.return_value = operation
    monkeypatch.setattr(google_provider.genai, "Client", lambda **_: fake_client)

    provider = GoogleVertexProvider()
    provider.generate_video(
        prompt="high-priority clip",
        model="veo-3.1-fast-generate-001",
    )

    assert fake_client.models.generate_videos.call_args.kwargs["model"] == "veo-3.1-fast-generate-001"


def test_generate_video_without_image_omits_source_image(monkeypatch):
    fake_client = MagicMock()
    operation = MagicMock()
    operation.done = True
    operation.error = None
    operation.result.generated_videos = [MagicMock(video=MagicMock())]
    fake_client.models.generate_videos.return_value = operation
    monkeypatch.setattr(google_provider.genai, "Client", lambda **_: fake_client)

    provider = GoogleVertexProvider()
    provider.generate_video(prompt="text-to-video only")

    source = fake_client.models.generate_videos.call_args.kwargs["source"]
    assert source.prompt == "text-to-video only"
    assert source.image is None


def test_generate_video_passes_gcs_image_for_image_to_video_conditioning(monkeypatch):
    fake_client = MagicMock()
    operation = MagicMock()
    operation.done = True
    operation.error = None
    operation.result.generated_videos = [MagicMock(video=MagicMock())]
    fake_client.models.generate_videos.return_value = operation
    monkeypatch.setattr(google_provider.genai, "Client", lambda **_: fake_client)

    provider = GoogleVertexProvider()
    gcs_uri = "gs://rss7-ai-media-genmedia/projects/ai-agent/images/2026/09/image_x.png"
    provider.generate_video(prompt="animate this image", image=gcs_uri)

    source = fake_client.models.generate_videos.call_args.kwargs["source"]
    assert source.image is not None
    assert source.image.gcs_uri == gcs_uri
    assert source.image.mime_type == "image/png"


def test_generate_video_guesses_mime_type_from_image_extension(monkeypatch):
    fake_client = MagicMock()
    operation = MagicMock()
    operation.done = True
    operation.error = None
    operation.result.generated_videos = [MagicMock(video=MagicMock())]
    fake_client.models.generate_videos.return_value = operation
    monkeypatch.setattr(google_provider.genai, "Client", lambda **_: fake_client)

    provider = GoogleVertexProvider()
    gcs_uri = "gs://rss7-ai-media-genmedia/projects/ai-agent/images/2026/09/image_x.jpg"
    provider.generate_video(prompt="animate this image", image=gcs_uri)

    source = fake_client.models.generate_videos.call_args.kwargs["source"]
    assert source.image.mime_type == "image/jpeg"
