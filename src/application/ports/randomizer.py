from __future__ import annotations

from typing import Protocol


class Randomizer(Protocol):
    def int_between(self, low: int, high_inclusive: int) -> int: ...
