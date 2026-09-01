"""環境変数（.env）からGoogle Cloud関連の設定を読み込む。"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]

_env_loaded = False


def load_env() -> None:
    """リポジトリルートの `.env` を読み込む（一度だけ）。ファイルが無ければ何もしない。"""
    global _env_loaded
    if _env_loaded:
        return
    load_dotenv(REPO_ROOT / ".env")
    _env_loaded = True


@dataclass(frozen=True)
class GoogleConfig:
    project: str
    location: str


def get_google_config() -> GoogleConfig:
    """Vertex AI (Google Gen AI SDK) 接続に必要な設定を読み込む。

    認証情報そのもの（APIキー・サービスアカウント鍵など）はここでは扱わない。
    Application Default Credentials（`gcloud auth application-default login`）か、
    環境変数 `GOOGLE_APPLICATION_CREDENTIALS` を通じてSDK側が自動的に解決する。
    """
    load_env()
    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "").strip()
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1").strip() or "us-central1"

    if not project:
        raise RuntimeError(
            "環境変数 GOOGLE_CLOUD_PROJECT が設定されていません。"
            " .env.example を `.env` にコピーし、GOOGLE_CLOUD_PROJECT=rss7-ai-media を設定してください。"
        )

    return GoogleConfig(project=project, location=location)
