from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId


@dataclass(frozen=True, slots=True)
class GrowDickCommand:
    tg_user_id: TelegramUserId
    tg_username: str | None
    chat_id: TelegramChatId


@dataclass(frozen=True, slots=True)
class GrowDickResult:
    delta_cm: int
    new_size_cm: int


@dataclass(frozen=True, slots=True)
class GrowDickCooldown:
    remaining: timedelta
    current_size_cm: int
