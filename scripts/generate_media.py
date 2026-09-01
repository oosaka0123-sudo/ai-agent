#!/usr/bin/env python3
"""画像・動画生成AIを呼び出す共通CLI（今回はGoogle Vertex AI接続部分のみ）。

使い方:
    python scripts/generate_media.py --provider google --type image --prompt "..."
    python scripts/generate_media.py --provider google --type video --prompt "..." --aspect-ratio 9:16

事前準備:
    1. `cp .env.example .env` を実行し、`.env` に GOOGLE_CLOUD_PROJECT などを設定する。
    2. ローカル/コンテナで `gcloud auth application-default login` を実行するか、
       サービスアカウント鍵を用意して `.env` の GOOGLE_APPLICATION_CREDENTIALS に
       そのファイルパスを設定する（鍵ファイル自体はGitにコミットしない）。
    3. `pip install -r requirements.txt` を実行する。

生成物は `public/assets/ai/` に、実行ログは `logs/media-generation.jsonl` に保存される。
失敗時は自動的に1回だけ再試行し、2回失敗した時点でエラー内容を表示して停止する。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from media_gen.logging_utils import GenerationLogEntry, append_log  # noqa: E402
from media_gen.naming import build_output_path, extension_for_mime  # noqa: E402
from media_gen.providers.google_provider import GoogleVertexProvider  # noqa: E402
from media_gen.retry import run_with_retry  # noqa: E402

DEFAULT_OUTPUT_DIR = REPO_ROOT / "public" / "assets" / "ai"
DEFAULT_LOG_PATH = REPO_ROOT / "logs" / "media-generation.jsonl"

# 将来的に他プロバイダ（Gemini Developer API等）を追加する場合はここに登録する。
PROVIDERS = {
    "google": GoogleVertexProvider,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="generate_media.py",
        description="画像・動画生成AIを呼び出す共通CLI（Vertex AI接続基盤）",
    )
    parser.add_argument("--provider", required=True, choices=sorted(PROVIDERS), help="使用するプロバイダ")
    parser.add_argument("--type", required=True, choices=["image", "video"], help="生成する種類")
    parser.add_argument("--prompt", required=True, help="生成内容を指示するプロンプト")
    parser.add_argument("--model", default=None, help="使用するモデルID（省略時はプロバイダの既定モデル）")
    parser.add_argument("--aspect-ratio", default=None, help='アスペクト比（例: "1:1", "16:9", "9:16"）')
    parser.add_argument("--negative-prompt", default=None, help="生成物に含めたくない要素")
    parser.add_argument("--count", type=int, default=1, help="生成する枚数/本数（既定値: 1）")
    parser.add_argument(
        "--output-mime-type",
        default="image/png",
        help="画像のMIMEタイプ（画像生成のみ。既定値: image/png）",
    )
    parser.add_argument("--duration-seconds", type=int, default=None, help="動画の長さ（秒、動画生成のみ）")
    parser.add_argument("--poll-interval", type=float, default=15.0, help="動画生成の状態確認間隔（秒、既定値: 15）")
    parser.add_argument("--timeout", type=float, default=600.0, help="動画生成の最大待機時間（秒、既定値: 600）")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="生成物の保存先ディレクトリ")
    parser.add_argument("--log-file", type=Path, default=DEFAULT_LOG_PATH, help="実行ログ（JSONL）の保存先")
    return parser


def _relative_to_repo(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    provider_cls = PROVIDERS[args.provider]

    try:
        provider = provider_cls()
    except Exception as exc:
        append_log(
            args.log_file,
            GenerationLogEntry(
                provider=args.provider,
                model=args.model or "(初期化前)",
                type=args.type,
                prompt=args.prompt,
                status="failed",
                output_path=[],
                error=str(exc),
            ),
        )
        print(f"[エラー] プロバイダの初期化に失敗しました: {exc}", file=sys.stderr)
        return 2

    def call_provider():
        if args.type == "image":
            return provider.generate_image(
                prompt=args.prompt,
                model=args.model,
                count=args.count,
                aspect_ratio=args.aspect_ratio,
                negative_prompt=args.negative_prompt,
                output_mime_type=args.output_mime_type,
            )
        return provider.generate_video(
            prompt=args.prompt,
            model=args.model,
            count=args.count,
            aspect_ratio=args.aspect_ratio,
            negative_prompt=args.negative_prompt,
            duration_seconds=args.duration_seconds,
            poll_interval=args.poll_interval,
            timeout=args.timeout,
        )

    def on_attempt_failed(attempt: int, exc: Exception) -> None:
        print(f"[警告] {attempt}回目の生成に失敗しました: {exc}", file=sys.stderr)

    retry_result = run_with_retry(call_provider, max_attempts=2, on_attempt_failed=on_attempt_failed)

    if not retry_result.success:
        append_log(
            args.log_file,
            GenerationLogEntry(
                provider=args.provider,
                model=args.model or "(既定モデル)",
                type=args.type,
                prompt=args.prompt,
                status="failed",
                output_path=[],
                error=str(retry_result.error),
            ),
        )
        print(
            f"[エラー] {retry_result.attempts}回試行しましたが生成に失敗しました: {retry_result.error}",
            file=sys.stderr,
        )
        return 1

    generation = retry_result.value
    default_extension = "mp4" if args.type == "video" else "png"

    output_paths: List[Path] = []
    for index, asset in enumerate(generation.assets):
        extension = extension_for_mime(getattr(asset, "mime_type", None), default_extension)
        path = build_output_path(args.output_dir, args.type, extension, index=index)
        asset.save(str(path))
        output_paths.append(path)

    append_log(
        args.log_file,
        GenerationLogEntry(
            provider=args.provider,
            model=generation.model,
            type=args.type,
            prompt=args.prompt,
            status="success",
            output_path=[_relative_to_repo(p) for p in output_paths],
            error=None,
        ),
    )

    print(f"生成が完了しました（{len(output_paths)}件）:")
    for path in output_paths:
        print(f"  - {_relative_to_repo(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
