"""失敗時に1回だけ自動リトライする共通処理（2回失敗したら呼び出し元へエラーを返す）。"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass
class RetryResult(Generic[T]):
    value: Optional[T]
    attempts: int
    error: Optional[Exception]

    @property
    def success(self) -> bool:
        return self.error is None


def run_with_retry(
    func: Callable[[], T],
    max_attempts: int = 2,
    backoff_seconds: float = 3.0,
    on_attempt_failed: Optional[Callable[[int, Exception], None]] = None,
) -> RetryResult[T]:
    """`func` を最大 `max_attempts` 回まで実行する（既定: 初回1回＋自動リトライ1回）。"""
    last_error: Optional[Exception] = None
    for attempt in range(1, max_attempts + 1):
        try:
            return RetryResult(value=func(), attempts=attempt, error=None)
        except Exception as exc:  # noqa: BLE001 - エラー内容を呼び出し元・ログへ伝える
            last_error = exc
            if on_attempt_failed:
                on_attempt_failed(attempt, exc)
            if attempt < max_attempts:
                time.sleep(backoff_seconds)
    return RetryResult(value=None, attempts=max_attempts, error=last_error)
