from __future__ import annotations

from dataclasses import dataclass

from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId


@dataclass(frozen=True, slots=True)
class GiftSizeCommand:
    chat_id: TelegramChatId
    actor_tg_id: TelegramUserId
    actor_username: str | None
    target_tg_id: TelegramUserId
    target_username: str | None
    amount_cm: int


@dataclass(frozen=True, slots=True)
class GiftSizeResult:
    amount_cm: int
    actor_new_size_cm: int
    target_new_size_cm: int
