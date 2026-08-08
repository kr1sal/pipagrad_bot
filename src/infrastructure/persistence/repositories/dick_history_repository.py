from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.dick_history_entry import DickHistoryEntry
from src.domain.value_objects.dick_history_reason import DickHistoryReason
from src.domain.value_objects.telegram_ids import TelegramChatId
from src.infrastructure.persistence.models import DickHistoryModel


class SqlAlchemyDickHistoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entry: DickHistoryEntry) -> DickHistoryEntry:
        model = DickHistoryModel(
            user_id=entry.user_id,
            chat_id=int(entry.chat_id),
            delta_cm=entry.delta_cm,
            new_size_cm=entry.new_size_cm,
            reason=entry.reason.value,
            created_at=entry.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return DickHistoryEntry(
            id=model.id,
            user_id=entry.user_id,
            chat_id=entry.chat_id,
            delta_cm=entry.delta_cm,
            new_size_cm=entry.new_size_cm,
            reason=entry.reason,
            created_at=entry.created_at,
        )

    async def list_page(
        self, user_id: int, chat_id: TelegramChatId, *, limit: int, offset: int
    ) -> list[DickHistoryEntry]:
        stmt = (
            select(DickHistoryModel)
            .where(
                DickHistoryModel.user_id == user_id,
                DickHistoryModel.chat_id == int(chat_id),
            )
            .order_by(DickHistoryModel.created_at.desc(), DickHistoryModel.id.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await self._session.scalars(stmt)).all()
        return [_to_entity(r) for r in rows]


def _to_entity(model: DickHistoryModel) -> DickHistoryEntry:
    return DickHistoryEntry(
        id=model.id,
        user_id=model.user_id,
        chat_id=TelegramChatId(model.chat_id),
        delta_cm=model.delta_cm,
        new_size_cm=model.new_size_cm,
        reason=DickHistoryReason(model.reason),
        created_at=model.created_at,
    )
