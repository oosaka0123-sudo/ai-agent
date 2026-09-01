"""`logs/media-generation.jsonl` への実行結果の記録。"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class GenerationLogEntry:
    provider: str
    model: str
    type: str
    prompt: str
    status: str
    output_path: list = field(default_factory=list)
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "provider": self.provider,
            "model": self.model,
            "type": self.type,
            "prompt": self.prompt,
            "status": self.status,
            "output_path": self.output_path,
            "error": self.error,
        }


def append_log(log_path: Path, entry: GenerationLogEntry) -> None:
    """1件のログをJSON Lines形式で追記する。`logs/` は `.gitignore` 済み。"""
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
