from __future__ import annotations

from datetime import datetime

from src.application.ports.unit_of_work import UnitOfWork
from src.domain.entities.dick_history_entry import DickHistoryEntry
from src.domain.value_objects.dick_history_reason import DickHistoryReason
from src.domain.value_objects.telegram_ids import TelegramChatId


async def record(
    uow: UnitOfWork,
    *,
    user_id: int,
    chat_id: TelegramChatId,
    delta_cm: int,
    new_size_cm: int,
    reason: DickHistoryReason,
    now: datetime,
) -> None:
    """Log a dick-size change. No-op for zero-delta changes (nothing to show)."""
    if delta_cm == 0:
        return
    await uow.dick_history.add(
        DickHistoryEntry(
            id=None,
            user_id=user_id,
            chat_id=chat_id,
            delta_cm=delta_cm,
            new_size_cm=new_size_cm,
            reason=reason,
            created_at=now,
        )
    )
