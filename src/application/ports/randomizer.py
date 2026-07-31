from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, TypeVar

T = TypeVar("T")


class Randomizer(Protocol):
    def int_between(self, low: int, high_inclusive: int) -> int: ...

    def choice(self, seq: Sequence[T]) -> T: ...

    def sample(self, seq: Sequence[T], k: int) -> list[T]: ...
