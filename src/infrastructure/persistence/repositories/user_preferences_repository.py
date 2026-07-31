from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.value_objects.interaction_type import InteractionType
from src.domain.value_objects.telegram_ids import TelegramChatId
from src.domain.value_objects.user_preferences import UserPreferences
from src.infrastructure.persistence.models import UserPreferencesModel


class SqlAlchemyUserPreferencesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(
        self, user_id: int, chat_id: TelegramChatId
    ) -> UserPreferences | None:
        stmt = select(UserPreferencesModel).where(
            UserPreferencesModel.user_id == user_id,
            UserPreferencesModel.chat_id == int(chat_id),
        )
        row = await self._session.scalar(stmt)
        return _to_vo(row) if row else None

    async def upsert(
        self,
        user_id: int,
        chat_id: TelegramChatId,
        prefs: UserPreferences,
    ) -> None:
        values = {
            "user_id": user_id,
            "chat_id": int(chat_id),
            "allow_pet": InteractionType.PET in prefs.allowed,
            "allow_kiss": InteractionType.KISS in prefs.allowed,
            "allow_fuck": InteractionType.FUCK in prefs.allowed,
        }
        stmt = pg_insert(UserPreferencesModel).values(**values)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_prefs_user_chat",
            set_={
                "allow_pet": stmt.excluded.allow_pet,
                "allow_kiss": stmt.excluded.allow_kiss,
                "allow_fuck": stmt.excluded.allow_fuck,
            },
        )
        await self._session.execute(stmt)


def _to_vo(model: UserPreferencesModel) -> UserPreferences:
    allowed: set[InteractionType] = set()
    if model.allow_pet:
        allowed.add(InteractionType.PET)
    if model.allow_kiss:
        allowed.add(InteractionType.KISS)
    if model.allow_fuck:
        allowed.add(InteractionType.FUCK)
    return UserPreferences(allowed=frozenset(allowed))
