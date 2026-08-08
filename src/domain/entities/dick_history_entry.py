from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.domain.value_objects.dick_history_reason import DickHistoryReason
from src.domain.value_objects.telegram_ids import TelegramChatId


@dataclass(frozen=True, slots=True)
class DickHistoryEntry:
    """One recorded change to a user's dick size within a chat scope."""

    id: int | None
    user_id: int
    chat_id: TelegramChatId
    delta_cm: int
    new_size_cm: int
    reason: DickHistoryReason
    created_at: datetime
