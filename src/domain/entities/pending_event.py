from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from src.domain.value_objects.telegram_ids import TelegramChatId


class PendingEventKind(str, Enum):
    ORGY = "orgy"
    BOT_BATTLE = "bot_battle"
    TEAM_BATTLE = "team_battle"


# Orgy
ORGY_TIMER_MINUTES = 15
ORGY_COST_ML = 10
ORGY_BONUS_CM = 2

# Bot battle
BOT_BATTLE_TIMER_MINUTES = 5
BOT_BATTLE_BASE_POT = 100

# Team battle (/battle join window, opens once the opponent accepts)
TEAM_BATTLE_TIMER_MINUTES = 1


@dataclass(slots=True)
class PendingEvent:
    """
    A chat event that isn't resolved immediately: it's announced with an inline
    keyboard, players interact with it for a window of time (join/leave, pick a
    side), and a scheduler tick resolves it when `resolves_at` passes.

    `payload` is a free-form dict persisted as JSON so we can evolve per-kind
    fields without a migration per event type. Each kind has its own shape,
    documented next to the use case that reads/writes it.
    """

    id: int | None
    chat_id: TelegramChatId
    kind: PendingEventKind
    chat_message_id: int
    resolves_at: datetime
    created_at: datetime
    payload: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def new(
        cls,
        chat_id: TelegramChatId,
        kind: PendingEventKind,
        chat_message_id: int,
        resolves_at: datetime,
        now: datetime,
        payload: dict[str, Any] | None = None,
    ) -> PendingEvent:
        return cls(
            id=None,
            chat_id=chat_id,
            kind=kind,
            chat_message_id=chat_message_id,
            resolves_at=resolves_at,
            created_at=now,
            payload=payload or {},
        )
