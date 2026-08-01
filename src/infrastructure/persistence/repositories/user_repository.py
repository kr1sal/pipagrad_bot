from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import User
from src.domain.value_objects.telegram_ids import TelegramUserId
from src.infrastructure.persistence.models import UserModel


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_tg_id(self, tg_id: TelegramUserId) -> User | None:
        stmt = select(UserModel).where(UserModel.tg_id == int(tg_id))
        row = await self._session.scalar(stmt)
        return _to_entity(row) if row else None

    async def get_by_id(self, user_id: int) -> User | None:
        row = await self._session.get(UserModel, user_id)
        return _to_entity(row) if row else None

    async def get_by_username(self, username: str) -> User | None:
        stmt = select(UserModel).where(
            func.lower(UserModel.username) == username.lower()
        )
        row = await self._session.scalar(stmt)
        return _to_entity(row) if row else None

    async def add(self, user: User) -> User:
        model = UserModel(
            tg_id=int(user.tg_id),
            username=user.username,
            created_at=user.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        user.id = model.id
        return user


def _to_entity(model: UserModel) -> User:
    return User(
        id=model.id,
        tg_id=TelegramUserId(model.tg_id),
        username=model.username,
        created_at=model.created_at,
    )
