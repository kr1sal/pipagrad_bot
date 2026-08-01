from __future__ import annotations

from enum import Enum


class InteractionType(str, Enum):
    PET = "pet"
    KISS = "kiss"
    FUCK = "fuck"
    HUG = "hug"
