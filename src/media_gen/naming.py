"""生成物の保存先パス（日時＋種類で重複しないファイル名）を組み立てる。"""
from __future__ import annotations

import mimetypes
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional


def build_output_path(output_dir: Path, media_type: str, extension: str, index: int = 0) -> Path:
    """`{種類}_{日時}_{乱数}[-{枚数番号}].{拡張子}` の形式で保存先パスを作る。

    日時（秒単位）だけでは同一秒内に複数生成した場合に衝突しうるため、
    短い乱数（uuid4の先頭8文字）を組み合わせて重複を防いでいる。
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    unique = uuid.uuid4().hex[:8]
    suffix = f"-{index}" if index else ""
    filename = f"{media_type}_{timestamp}_{unique}{suffix}.{extension}"
    return output_dir / filename


def extension_for_mime(mime_type: Optional[str], default: str) -> str:
    """MIMEタイプから拡張子を推定する。判定できない場合は `default` を返す。"""
    if not mime_type:
        return default
    guessed = mimetypes.guess_extension(mime_type)
    if not guessed:
        return default
    return guessed.lstrip(".")
