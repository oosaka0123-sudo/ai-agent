"""src/media_gen/logging_utils.py のテスト（ネットワーク接続不要）。"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from media_gen.logging_utils import GenerationLogEntry, append_log  # noqa: E402


def test_append_log_writes_jsonl_with_required_fields(tmp_path):
    log_path = tmp_path / "logs" / "media-generation.jsonl"

    append_log(
        log_path,
        GenerationLogEntry(
            provider="google",
            model="imagen-3.0-generate-002",
            type="image",
            prompt="テスト用プロンプト",
            status="success",
            output_path=["public/assets/ai/image_1.png"],
            error=None,
        ),
    )
    append_log(
        log_path,
        GenerationLogEntry(
            provider="google",
            model="veo-2.0-generate-001",
            type="video",
            prompt="テスト用プロンプト2",
            status="failed",
            output_path=[],
            error="timeout",
        ),
    )

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2

    first = json.loads(lines[0])
    for key in ("timestamp", "provider", "model", "type", "prompt", "status", "output_path", "error"):
        assert key in first
    assert first["status"] == "success"
    assert first["output_path"] == ["public/assets/ai/image_1.png"]

    second = json.loads(lines[1])
    assert second["status"] == "failed"
    assert second["error"] == "timeout"
