from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.domain.value_objects.telegram_ids import TelegramUserId


@dataclass(slots=True)
class User:
    id: int | None
    tg_id: TelegramUserId
    username: str | None
    created_at: datetime

    @classmethod
    def new(cls, tg_id: TelegramUserId, username: str | None, now: datetime) -> User:
        return cls(id=None, tg_id=tg_id, username=username, created_at=now)
