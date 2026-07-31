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
class UserGlobalStats:
    chats_count: int
    total_cm: int
    max_cm: int
