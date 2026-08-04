from __future__ import annotations

from dataclasses import dataclass

from src.domain.value_objects.telegram_ids import TelegramUserId


@dataclass(frozen=True, slots=True)
class TopEntry:
    rank: int
    tg_id: TelegramUserId
    username: str | None
    size_cm: int


@dataclass(frozen=True, slots=True)
class MyChatBalance:
    dick_size_cm: int
    semen_current_ml: int
    semen_cap_ml: int
    regen_per_hour: int
