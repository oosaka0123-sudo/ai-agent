"""Google Vertex AI（公式 `google-genai` SDK）を使った画像・動画生成。

画像は Imagen（`client.models.generate_images`）、動画は Veo（`client.models.generate_videos`）
を呼び出す。動画生成は非同期のロングランニングオペレーションなので、
ジョブ開始 → `client.operations.get` で状態確認 → 完了、の流れをここで吸収する。

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
DEFAULT_IMAGE_MODEL = "imagen-3.0-generate-002"
DEFAULT_VIDEO_MODEL = "veo-2.0-generate-001"


class GoogleVertexProvider:
    """Vertex AI 上の Imagen（画像）・Veo（動画）を呼び出すプロバイダ。"""

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

        # 注: SDK側で generate_images は将来的に非推奨（2027年1月以降に削除予定、
        # generate_content + 画像モデルへの移行が案内されている）。現時点では
        # Imagen系モデルへの最も直接的な呼び出し方法なのでそのまま使用している。
        response = self._client.models.generate_images(
            model=resolved_model,
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=count,
                aspect_ratio=aspect_ratio,
                negative_prompt=negative_prompt,
                output_mime_type=output_mime_type,
            ),
        )

        if not response.generated_images:
            raise RuntimeError(
                "画像が生成されませんでした（安全フィルター等で除外された可能性があります）。"
            )

        return GenerationResult(
            model=resolved_model,
            assets=[generated.image for generated in response.generated_images],
        )

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
