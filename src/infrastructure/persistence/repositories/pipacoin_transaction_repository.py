from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.pipacoin_transaction import PipaCoinTransaction
from src.domain.value_objects.pipacoin_transaction_kind import (
    PipaCoinTransactionKind,
)
from src.infrastructure.persistence.models import PipaCoinTransactionModel


class SqlAlchemyPipaCoinTransactionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, tx: PipaCoinTransaction) -> PipaCoinTransaction:
        model = PipaCoinTransactionModel(
            user_id=tx.user_id,
            delta=tx.delta,
            balance_after=tx.balance_after,
            kind=tx.kind.value,
            counterparty_user_id=tx.counterparty_user_id,
            created_at=tx.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return PipaCoinTransaction(
            id=model.id,
            user_id=tx.user_id,
            delta=tx.delta,
            balance_after=tx.balance_after,
            kind=tx.kind,
            counterparty_user_id=tx.counterparty_user_id,
            created_at=tx.created_at,
        )

    async def list_page(
        self, user_id: int, *, limit: int, offset: int
    ) -> list[PipaCoinTransaction]:
        stmt = (
            select(PipaCoinTransactionModel)
            .where(PipaCoinTransactionModel.user_id == user_id)
            .order_by(
                PipaCoinTransactionModel.created_at.desc(),
                PipaCoinTransactionModel.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        rows = (await self._session.scalars(stmt)).all()
        return [_to_entity(r) for r in rows]


def _to_entity(model: PipaCoinTransactionModel) -> PipaCoinTransaction:
    return PipaCoinTransaction(
        id=model.id,
        user_id=model.user_id,
        delta=model.delta,
        balance_after=model.balance_after,
        kind=PipaCoinTransactionKind(model.kind),
        counterparty_user_id=model.counterparty_user_id,
        created_at=model.created_at,
    )
