from __future__ import annotations

from dataclasses import dataclass

from src.domain.value_objects.interaction_type import InteractionType
from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId


@dataclass(frozen=True, slots=True)
class EnsureGroupRegisteredCommand:
    chat_id: TelegramChatId
    title: str | None
    added_by_tg_id: TelegramUserId | None


class SettingsChange:
    """Sealed base class for atomic settings changes."""


@dataclass(frozen=True, slots=True)
class ToggleBattles(SettingsChange):
    pass


@dataclass(frozen=True, slots=True)
class ToggleRandomEvents(SettingsChange):
    pass


@dataclass(frozen=True, slots=True)
class ToggleInteraction(SettingsChange):
    kind: InteractionType


@dataclass(frozen=True, slots=True)
class UpdateGroupSettingsCommand:
    chat_id: TelegramChatId
    actor_tg_id: TelegramUserId
    change: SettingsChange
