"""Google Cloud Storage as the durable home for every generated asset.

The MCP server's own filesystem (including Cloud Run's local disk) is never
a permanent store: every asset is uploaded to GCS immediately after
generation, under a per-project, per-type, per-month layout, and the local
scratch copy is discarded.

Layout (see docs/GOOGLE_MEDIA_MCP.md):
    projects/{project_slug}/images/YYYY/MM/{filename}
    projects/{project_slug}/videos/YYYY/MM/{filename}
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from media_gen.naming import build_output_path, extension_for_mime  # noqa: E402

_TYPE_DIR = {"image": "images", "video": "videos"}


def build_gcs_object_path(project_slug: str, media_type: str, filename: str) -> str:
    """`projects/{slug}/images|videos/YYYY/MM/{filename}`"""
    type_dir = _TYPE_DIR.get(media_type)
    if not type_dir:
        raise ValueError(f"unknown media_type: {media_type!r} (expected 'image' or 'video')")
    now = datetime.now(timezone.utc)
    return f"projects/{project_slug}/{type_dir}/{now:%Y}/{now:%m}/{filename}"


def build_local_scratch_path(scratch_dir: Path, media_type: str, mime_type: Optional[str], index: int = 0) -> Path:
    """A throwaway local path to write to before uploading to GCS."""
    default_extension = "mp4" if media_type == "video" else "png"
    extension = extension_for_mime(mime_type, default_extension)
    return build_output_path(scratch_dir, media_type, extension, index=index)


class GcsUploader:
    """Thin wrapper around `google.cloud.storage` so it can be swapped for a
    fake in tests without importing the real SDK (which needs credentials)."""

    def __init__(self, bucket_name: str) -> None:
        self._bucket_name = bucket_name
        self._client = None  # lazy: constructed on first real upload

    def _bucket(self):
        if self._client is None:
            from google.cloud import storage  # deferred: avoid requiring ADC at import time

            self._client = storage.Client()
        return self._client.bucket(self._bucket_name)

    def upload_file(self, local_path: Path, object_path: str, content_type: Optional[str] = None) -> str:
        """Uploads `local_path` to `object_path` in the bucket. Returns the `gs://` URI."""
        blob = self._bucket().blob(object_path)
        blob.upload_from_filename(str(local_path), content_type=content_type)
        return f"gs://{self._bucket_name}/{object_path}"

    def signed_url(self, object_path: str, expiration_seconds: int = 7 * 24 * 3600) -> Optional[str]:
        """Best-effort: a v4 signed URL for temporary read access. Returns None if
        signing isn't possible in this environment (e.g. ADC without a service
        account that supports signing) rather than raising — the `gs://` URI is
        always returned regardless, so this is a convenience, not a requirement."""
        try:
            from datetime import timedelta

            blob = self._bucket().blob(object_path)
            return blob.generate_signed_url(version="v4", expiration=timedelta(seconds=expiration_seconds), method="GET")
        except Exception:  # noqa: BLE001 - signing is best-effort by design
            return None
