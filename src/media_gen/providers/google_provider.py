"""Google Vertex AI（公式 `google-genai` SDK）を使った画像・動画生成。

画像は Gemini（`client.models.generate_content` + `response_modalities=["IMAGE"]`）、
動画は Veo（`client.models.generate_videos`）を呼び出す。動画生成は非同期の
ロングランニングオペレーションなので、通常の同期ヘルパーに加えて
「開始」と「状態確認」を分離した resumable API も提供する。

認証情報はコードに直接書かない。`genai.Client(vertexai=True, ...)` は
Application Default Credentials（`gcloud auth application-default login`）や
環境変数 `GOOGLE_APPLICATION_CREDENTIALS` を通じてSDKが自動的に解決する。
"""
from __future__ import annotations

import mimetypes
import time
from typing import Optional

from google import genai
from google.genai import types

from ..config import get_google_config
from .base import GenerationResult

DEFAULT_IMAGE_MODEL = "gemini-2.5-flash-image"
DEFAULT_VIDEO_MODEL = "veo-3.1-fast-generate-001"


class GoogleVertexProvider:
    """Vertex AI 上の Gemini（画像）・Veo（動画）を呼び出すプロバイダ。"""

    name = "google"

    def __init__(self) -> None:
        config = get_google_config()
        self._client = genai.Client(
            vertexai=True,
            project=config.project,
            location=config.location,
        )

    def generate_image(
        self,
        *,
        prompt: str,
        model: Optional[str] = None,
        count: int = 1,
        aspect_ratio: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        output_mime_type: str = "image/png",
        **_: object,
    ) -> GenerationResult:
        resolved_model = model or DEFAULT_IMAGE_MODEL

        full_prompt = prompt
        if negative_prompt:
            full_prompt = f"{prompt}\n\nAvoid: {negative_prompt}"

        response = self._client.models.generate_content(
            model=resolved_model,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                candidate_count=count,
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                    output_mime_type=output_mime_type,
                ),
            ),
        )

        assets = []
        for candidate in response.candidates or []:
            content = candidate.content
            if content is None:
                continue
            for part in content.parts or []:
                if part.inline_data is not None:
                    assets.append(
                        types.Image(
                            image_bytes=part.inline_data.data,
                            mime_type=part.inline_data.mime_type or output_mime_type,
                        )
                    )

        if not assets:
            raise RuntimeError(
                "画像が生成されませんでした（安全フィルター等で除外された可能性があります）。"
            )

        return GenerationResult(model=resolved_model, assets=assets)

    @staticmethod
    def _video_source(prompt: str, image: Optional[str]) -> types.GenerateVideosSource:
        source_image = None
        if image:
            guessed_mime_type, _ = mimetypes.guess_type(image)
            source_image = types.Image(
                gcs_uri=image,
                mime_type=guessed_mime_type or "image/png",
            )
        return types.GenerateVideosSource(prompt=prompt, image=source_image)

    def start_video_generation(
        self,
        *,
        prompt: str,
        model: Optional[str] = None,
        count: int = 1,
        aspect_ratio: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        duration_seconds: Optional[int] = None,
        image: Optional[str] = None,
        **_: object,
    ) -> dict[str, str]:
        """Start a Veo long-running operation and return immediately.

        The returned operation name is safe to persist and can be passed to
        :meth:`check_video_generation` from a later MCP request. This is the
        resumable path used when an MCP client has a shorter request timeout
        than Veo's generation latency.
        """
        resolved_model = model or DEFAULT_VIDEO_MODEL
        operation = self._client.models.generate_videos(
            model=resolved_model,
            source=self._video_source(prompt, image),
            config=types.GenerateVideosConfig(
                number_of_videos=count,
                aspect_ratio=aspect_ratio,
                negative_prompt=negative_prompt,
                duration_seconds=duration_seconds,
            ),
        )
        if not operation.name:
            raise RuntimeError("動画生成ジョブのoperation nameを取得できませんでした。")
        return {"model": resolved_model, "operation_name": operation.name}

    def check_video_generation(
        self,
        *,
        operation_name: str,
        model: Optional[str] = None,
    ) -> dict[str, object]:
        """Check one Veo operation without blocking for completion."""
        if not operation_name or "/operations/" not in operation_name:
            raise ValueError("有効なVeo operation nameが必要です。")

        operation = types.GenerateVideosOperation(name=operation_name)
        operation = self._client.operations.get(operation)

        if not operation.done:
            return {
                "status": "processing",
                "operation_name": operation_name,
                "model": model or DEFAULT_VIDEO_MODEL,
            }

        if operation.error:
            raise RuntimeError(f"動画生成ジョブが失敗しました: {operation.error}")

        result = operation.result
        if not result or not result.generated_videos:
            raise RuntimeError(
                "動画が生成されませんでした（安全フィルター等で除外された可能性があります）。"
            )

        generation = GenerationResult(
            model=model or DEFAULT_VIDEO_MODEL,
            assets=[generated.video for generated in result.generated_videos],
        )
        return {
            "status": "success",
            "operation_name": operation_name,
            "model": generation.model,
            "generation": generation,
        }

    def generate_video(
        self,
        *,
        prompt: str,
        model: Optional[str] = None,
        count: int = 1,
        aspect_ratio: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        duration_seconds: Optional[int] = None,
        image: Optional[str] = None,
        poll_interval: float = 15.0,
        timeout: float = 600.0,
        **_: object,
    ) -> GenerationResult:
        """Backward-compatible synchronous wrapper around the resumable API."""
        started = self.start_video_generation(
            prompt=prompt,
            model=model,
            count=count,
            aspect_ratio=aspect_ratio,
            negative_prompt=negative_prompt,
            duration_seconds=duration_seconds,
            image=image,
        )
        operation_name = started["operation_name"]
        resolved_model = started["model"]

        start = time.monotonic()
        while True:
            checked = self.check_video_generation(
                operation_name=operation_name,
                model=resolved_model,
            )
            if checked["status"] == "success":
                return checked["generation"]  # type: ignore[return-value]
            if time.monotonic() - start > timeout:
                raise TimeoutError(
                    f"動画生成が{timeout:.0f}秒以内に完了しませんでした"
                    f"（ジョブ名: {operation_name}）。"
                )
            time.sleep(poll_interval)
