from __future__ import annotations

from dataclasses import dataclass

from src.domain.services.interaction_policy import Denial
from src.domain.value_objects.interaction_type import InteractionType
from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId


@dataclass(frozen=True, slots=True)
class PerformInteractionCommand:
    chat_id: TelegramChatId
    actor_tg_id: TelegramUserId
    actor_username: str | None
    target_tg_id: TelegramUserId
    target_username: str | None
    kind: InteractionType


@dataclass(frozen=True, slots=True)
class InteractionPerformed:
    kind: InteractionType
    actor_tg_id: TelegramUserId
    target_tg_id: TelegramUserId


@dataclass(frozen=True, slots=True)
class InteractionDenied:
    kind: InteractionType
    reason: Denial


@dataclass(frozen=True, slots=True)
class ToggleMyPreferenceCommand:
    tg_user_id: TelegramUserId
    tg_username: str | None
    chat_id: TelegramChatId
    kind: InteractionType


@dataclass(frozen=True, slots=True)
class GetMyPreferencesCommand:
    tg_user_id: TelegramUserId
    tg_username: str | None
    chat_id: TelegramChatId
