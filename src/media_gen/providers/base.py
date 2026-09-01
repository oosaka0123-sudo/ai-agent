"""メディア生成プロバイダの共通の戻り値の型。

各プロバイダ（`google_provider.GoogleVertexProvider` など）は、
`generate_image` / `generate_video` メソッドで `GenerationResult` を返す。
`assets` の各要素は `mime_type` 属性と `save(path: str)` メソッドを持つこと
（google-genai SDKの `types.Image` / `types.Video` はどちらも満たす）。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List


@dataclass
class GenerationResult:
    model: str
    assets: List[Any]
