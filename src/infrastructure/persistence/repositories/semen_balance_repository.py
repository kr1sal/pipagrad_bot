from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.semen_balance import SemenBalance
from src.domain.value_objects.telegram_ids import TelegramChatId
from src.infrastructure.persistence.models import SemenBalanceModel


class SqlAlchemySemenBalanceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(
        self, user_id: int, chat_id: TelegramChatId
    ) -> SemenBalance | None:
        stmt = select(SemenBalanceModel).where(
            SemenBalanceModel.user_id == user_id,
            SemenBalanceModel.chat_id == int(chat_id),
        )
        row = await self._session.scalar(stmt)
        return _to_entity(row) if row else None

    async def upsert(self, balance: SemenBalance) -> SemenBalance:
        stmt = pg_insert(SemenBalanceModel).values(
            user_id=balance.user_id,
            chat_id=int(balance.chat_id),
            stored_ml=balance.stored_ml,
            updated_at=balance.updated_at,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_semen_user_chat",
            set_={
                "stored_ml": stmt.excluded.stored_ml,
                "updated_at": stmt.excluded.updated_at,
            },
        ).returning(SemenBalanceModel.id)
        result = await self._session.execute(stmt)
        balance.id = result.scalar_one()
        return balance


def _to_entity(model: SemenBalanceModel) -> SemenBalance:
    return SemenBalance(
        id=model.id,
        user_id=model.user_id,
        chat_id=TelegramChatId(model.chat_id),
        stored_ml=model.stored_ml,
        updated_at=model.updated_at,
    )
