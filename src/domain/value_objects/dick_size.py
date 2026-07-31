from __future__ import annotations

from dataclasses import dataclass

MIN_SIZE_CM = 0
MAX_SIZE_CM = 10_000


@dataclass(frozen=True, slots=True, order=True)
class DickSize:
    cm: int

    def __post_init__(self) -> None:
        if not MIN_SIZE_CM <= self.cm <= MAX_SIZE_CM:
            raise ValueError(f"DickSize out of range: {self.cm}")

    def apply(self, delta_cm: int) -> DickSize:
        new_value = max(MIN_SIZE_CM, min(MAX_SIZE_CM, self.cm + delta_cm))
        return DickSize(new_value)

    def __str__(self) -> str:
        return f"{self.cm} см"
