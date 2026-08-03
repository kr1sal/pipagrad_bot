from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.pending_event import PendingEvent, PendingEventKind
from src.domain.value_objects.telegram_ids import TelegramChatId
from src.infrastructure.persistence.models import PendingEventModel


class SqlAlchemyPendingEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, event: PendingEvent) -> PendingEvent:
        model = PendingEventModel(
            chat_id=int(event.chat_id),
            kind=event.kind.value,
            chat_message_id=event.chat_message_id,
            resolves_at=event.resolves_at,
            created_at=event.created_at,
            payload=event.payload,
        )
        self._session.add(model)
        await self._session.flush()
        event.id = model.id
        return event

    async def get(
        self, event_id: int, *, for_update: bool = False
    ) -> PendingEvent | None:
        row = await self._session.get(
            PendingEventModel, event_id, with_for_update=for_update
        )
        return _to_entity(row) if row else None

    async def list_ready(self, now: datetime) -> list[PendingEvent]:
        stmt = select(PendingEventModel).where(PendingEventModel.resolves_at <= now)
        rows = (await self._session.scalars(stmt)).all()
        return [_to_entity(m) for m in rows]

    async def update_payload(
        self, event_id: int, payload: dict[str, object]
    ) -> None:
        stmt = (
            update(PendingEventModel)
            .where(PendingEventModel.id == event_id)
            .values(payload=payload)
        )
        await self._session.execute(stmt)

    async def set_message_id(
        self, event_id: int, chat_message_id: int
    ) -> None:
        stmt = (
            update(PendingEventModel)
            .where(PendingEventModel.id == event_id)
            .values(chat_message_id=chat_message_id)
        )
        await self._session.execute(stmt)

    async def delete(self, event_id: int) -> None:
        stmt = delete(PendingEventModel).where(PendingEventModel.id == event_id)
        await self._session.execute(stmt)


def _to_entity(model: PendingEventModel) -> PendingEvent:
    return PendingEvent(
        id=model.id,
        chat_id=TelegramChatId(model.chat_id),
        kind=PendingEventKind(model.kind),
        chat_message_id=model.chat_message_id,
        resolves_at=model.resolves_at,
        created_at=model.created_at,
        payload=dict(model.payload or {}),
    )
