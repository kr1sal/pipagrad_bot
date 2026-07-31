from __future__ import annotations

import random
from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")


class SystemRandomizer:
    def __init__(self) -> None:
        self._rng = random.SystemRandom()

    def int_between(self, low: int, high_inclusive: int) -> int:
        if high_inclusive < low:
            raise ValueError("high must be >= low")
        return self._rng.randint(low, high_inclusive)

    def choice(self, seq: Sequence[T]) -> T:
        if not seq:
            raise IndexError("empty sequence")
        return self._rng.choice(list(seq))

    def sample(self, seq: Sequence[T], k: int) -> list[T]:
        return self._rng.sample(list(seq), k)
