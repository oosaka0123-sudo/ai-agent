"""Google Vertex AI（公式 `google-genai` SDK）を使った画像・動画生成。

画像は Gemini（`client.models.generate_content` + `response_modalities=["IMAGE"]`）、
動画は Veo（`client.models.generate_videos`）を呼び出す。動画生成は非同期の
ロングランニングオペレーションなので、ジョブ開始 → `client.operations.get`
で状態確認 → 完了、の流れをここで吸収する。

認証情報はコードに直接書かない。`genai.Client(vertexai=True, ...)` は
Application Default Credentials（`gcloud auth application-default login`）や
環境変数 `GOOGLE_APPLICATION_CREDENTIALS` を通じてSDKが自動的に解決する。
"""
from __future__ import annotations

import time
from typing import Optional

from google import genai
from google.genai import types

from ..config import get_google_config
from .base import GenerationResult

# 2026年時点でVertex AI上で利用できる代表的なモデル。
# モデルは頻繁に更新されるため、必要に応じて --model で上書きすること。
#
# 画像はImagen専用のgenerate_images ではなく、Gemini本体の
# generate_content（response_modalities=["IMAGE"]）を使う。旧
# imagen-3.0-generate-002 / imagen-4.0-generate-001 はプロジェクト
# rss7-ai-media のVertex AI上でPublisher Model 404を返し続けたため
# （Issue #43）、現行のモデル構成へ切り替えた。
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

        # Geminiのgenerate_contentには専用のnegative_prompt引数がないため、
        # プロンプト本文に折り込む。
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

    def generate_video(
        self,
        *,
        prompt: str,
        model: Optional[str] = None,
        count: int = 1,
        aspect_ratio: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        duration_seconds: Optional[int] = None,
        poll_interval: float = 15.0,
        timeout: float = 600.0,
        **_: object,
    ) -> GenerationResult:
        resolved_model = model or DEFAULT_VIDEO_MODEL

        # ジョブ開始（非同期のロングランニングオペレーション）
        operation = self._client.models.generate_videos(
            model=resolved_model,
            source=types.GenerateVideosSource(prompt=prompt),
            config=types.GenerateVideosConfig(
                number_of_videos=count,
                aspect_ratio=aspect_ratio,
                negative_prompt=negative_prompt,
                duration_seconds=duration_seconds,
            ),
        )

        # 状態確認 → 完了まで待機
        start = time.monotonic()
        while not operation.done:
            if time.monotonic() - start > timeout:
                raise TimeoutError(
                    f"動画生成が{timeout:.0f}秒以内に完了しませんでした"
                    f"（ジョブ名: {operation.name}）。"
                )
            time.sleep(poll_interval)
            operation = self._client.operations.get(operation)

        if operation.error:
            raise RuntimeError(f"動画生成ジョブが失敗しました: {operation.error}")

        result = operation.result
        if not result or not result.generated_videos:
            raise RuntimeError(
                "動画が生成されませんでした（安全フィルター等で除外された可能性があります）。"
            )

        return GenerationResult(
            model=resolved_model,
            assets=[generated.video for generated in result.generated_videos],
        )
