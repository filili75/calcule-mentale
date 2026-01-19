from __future__ import annotations

import random
from dataclasses import dataclass

from src.models import ExerciseSettings, LEVEL_PRESETS


@dataclass(frozen=True)
class Operation:
    sign: int
    value: int

    def text(self) -> str:
        symbol = "+" if self.sign >= 0 else "-"
        return f"{symbol}{self.value}"

    def apply(self, total: int) -> int:
        return total + (self.sign * self.value)


@dataclass(frozen=True)
class ExerciseSequence:
    operations: list[Operation]
    result: int
    initial_value: int


def _pick_value(min_value: int, max_value: int) -> int:
    return random.randint(min_value, max_value)


def generate_sequence(settings: ExerciseSettings) -> ExerciseSequence:
    level = LEVEL_PRESETS[settings.level_name]
    operations: list[Operation] = []

    total = 0
    max_total = 10 ** settings.columns - 1

    for _ in range(settings.operations_count):
        for _attempt in range(100):
            value = _pick_value(level.min_value, level.max_value)
            sign = random.choice([1, -1])
            next_total = total + sign * value

            if 0 <= next_total <= max_total:
                operations.append(Operation(sign=sign, value=value))
                total = next_total
                break
        else:
            operations.append(Operation(sign=1, value=level.min_value))
            total = min(max_total, total + level.min_value)

    return ExerciseSequence(operations=operations, result=total, initial_value=0)
