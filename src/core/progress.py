from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


APP_DIR_NAME = ".soroban_kids_trainer"
PROGRESS_FILE_NAME = "progress.json"


def get_progress_path() -> Path:
    return Path.home() / APP_DIR_NAME / PROGRESS_FILE_NAME


@dataclass
class ProgressStats:
    total_correct: int = 0
    total_wrong: int = 0
    total_time_s: float = 0.0

    def record_attempt(self, correct: bool, elapsed_s: float) -> None:
        if correct:
            self.total_correct += 1
        else:
            self.total_wrong += 1
        if elapsed_s > 0:
            self.total_time_s += elapsed_s

    @property
    def total_attempts(self) -> int:
        return self.total_correct + self.total_wrong

    def to_dict(self) -> dict:
        return {
            "total_correct": self.total_correct,
            "total_wrong": self.total_wrong,
            "total_time_s": round(self.total_time_s, 2),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProgressStats":
        return cls(
            total_correct=int(data.get("total_correct", 0)),
            total_wrong=int(data.get("total_wrong", 0)),
            total_time_s=float(data.get("total_time_s", 0.0)),
        )


def load_progress() -> ProgressStats:
    path = get_progress_path()
    if not path.exists():
        return ProgressStats()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return ProgressStats()

    if isinstance(data, dict):
        return ProgressStats.from_dict(data)

    return ProgressStats()


def save_progress(stats: ProgressStats) -> None:
    path = get_progress_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(stats.to_dict(), indent=2)
    path.write_text(payload, encoding="utf-8")
