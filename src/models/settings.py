from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LevelConfig:
    name: str
    min_value: int
    max_value: int
    min_ops: int
    max_ops: int
    default_ops: int
    delay_s: float


@dataclass
class ExerciseSettings:
    level_name: str
    columns: int
    operations_count: int
    delay_s: float


LEVEL_PRESETS: dict[str, LevelConfig] = {
    "Beginner": LevelConfig(
        name="Beginner",
        min_value=1,
        max_value=9,
        min_ops=5,
        max_ops=10,
        default_ops=8,
        delay_s=2.0,
    ),
    "Intermediate": LevelConfig(
        name="Intermediate",
        min_value=1,
        max_value=20,
        min_ops=10,
        max_ops=15,
        default_ops=12,
        delay_s=1.5,
    ),
    "Advanced": LevelConfig(
        name="Advanced",
        min_value=1,
        max_value=50,
        min_ops=20,
        max_ops=25,
        default_ops=20,
        delay_s=1.0,
    ),
    "Speed": LevelConfig(
        name="Speed",
        min_value=1,
        max_value=50,
        min_ops=20,
        max_ops=30,
        default_ops=20,
        delay_s=0.7,
    ),
}
