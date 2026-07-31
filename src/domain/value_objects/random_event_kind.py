from __future__ import annotations

from enum import Enum


class RandomEventKind(str, Enum):
    METEOR = "meteor"
    RADIATION = "radiation"
    SPONTANEOUS_BATTLE = "spontaneous_battle"
