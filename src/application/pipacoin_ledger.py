from __future__ import annotations

from datetime import datetime

from src.application.ports.unit_of_work import UnitOfWork
from src.domain.entities.pipacoin_transaction import PipaCoinTransaction
from src.domain.value_objects.pipacoin_transaction_kind import (
    PipaCoinTransactionKind,
)


async def record(
    uow: UnitOfWork,
    *,
    user_id: int,
    delta: int,
    balance_after: int,
    kind: PipaCoinTransactionKind,
    counterparty_user_id: int | None,
    now: datetime,
) -> None:
    await uow.pipacoin_transactions.add(
        PipaCoinTransaction(
            id=None,
            user_id=user_id,
            delta=delta,
            balance_after=balance_after,
            kind=kind,
            counterparty_user_id=counterparty_user_id,
            created_at=now,
        )
    )
