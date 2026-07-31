from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.dick import Dick
from src.domain.value_objects.dick_size import DickSize
from src.domain.value_objects.telegram_ids import TelegramChatId
from src.infrastructure.persistence.models import DickModel


class SqlAlchemyDickRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_id: int, chat_id: TelegramChatId) -> Dick | None:
        stmt = select(DickModel).where(
            DickModel.user_id == user_id,
            DickModel.chat_id == int(chat_id),
        )
        row = await self._session.scalar(stmt)
        return _to_entity(row) if row else None

    async def add(self, dick: Dick) -> Dick:
        model = DickModel(
            user_id=dick.user_id,
            chat_id=int(dick.chat_id),
            size_cm=dick.size.cm,
            last_grow_at=dick.last_grow_at,
        )
        self._session.add(model)
        await self._session.flush()
        dick.id = model.id
        return dick

    async def list_for_chat(self, chat_id: TelegramChatId) -> list[Dick]:
        stmt = select(DickModel).where(DickModel.chat_id == int(chat_id))
        rows = (await self._session.scalars(stmt)).all()
        return [_to_entity(r) for r in rows]

    async def list_top_for_chat(
        self, chat_id: TelegramChatId, limit: int
    ) -> list[Dick]:
        stmt = (
            select(DickModel)
            .where(DickModel.chat_id == int(chat_id))
            .order_by(DickModel.size_cm.desc(), DickModel.id.asc())
            .limit(limit)
        )
        rows = (await self._session.scalars(stmt)).all()
        return [_to_entity(r) for r in rows]

    async def list_all_for_user(self, user_id: int) -> list[Dick]:
        stmt = select(DickModel).where(DickModel.user_id == user_id)
        rows = (await self._session.scalars(stmt)).all()
        return [_to_entity(r) for r in rows]

    async def update(self, dick: Dick) -> None:
        assert dick.id is not None
        stmt = (
            update(DickModel)
            .where(DickModel.id == dick.id)
            .values(size_cm=dick.size.cm, last_grow_at=dick.last_grow_at)
        )
        await self._session.execute(stmt)


def _to_entity(model: DickModel) -> Dick:
    return Dick(
        id=model.id,
        user_id=model.user_id,
        chat_id=TelegramChatId(model.chat_id),
        size=DickSize(model.size_cm),
        last_grow_at=model.last_grow_at,
    )
