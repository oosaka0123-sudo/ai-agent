"""src/media_gen/retry.py のテスト（ネットワーク接続不要）。"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from media_gen.retry import run_with_retry  # noqa: E402


def test_success_on_first_attempt():
    result = run_with_retry(lambda: "ok", backoff_seconds=0)
    assert result.success
    assert result.value == "ok"
    assert result.attempts == 1


def test_success_after_one_retry():
    calls = {"count": 0}

    def flaky():
        calls["count"] += 1
        if calls["count"] < 2:
            raise RuntimeError("一時的な失敗")
        return "recovered"

    result = run_with_retry(flaky, max_attempts=2, backoff_seconds=0)
    assert result.success
    assert result.value == "recovered"
    assert result.attempts == 2
    assert calls["count"] == 2


def test_stops_after_two_failures():
    calls = {"count": 0}

    def always_fails():
        calls["count"] += 1
        raise RuntimeError(f"失敗{calls['count']}回目")

    failures = []
    result = run_with_retry(
        always_fails,
        max_attempts=2,
        backoff_seconds=0,
        on_attempt_failed=lambda attempt, exc: failures.append((attempt, str(exc))),
    )

    assert not result.success
    assert result.attempts == 2
    assert calls["count"] == 2  # 2回失敗したら止まる（3回目は試行しない）
    assert len(failures) == 2
    assert "失敗2回目" in str(result.error)
