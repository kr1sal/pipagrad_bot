from __future__ import annotations

from datetime import datetime

from src.application import pipacoin_ledger
from src.application.dto.pipacoin import (
    TransferPipaCoinCommand,
    TransferPipaCoinResult,
)
from src.application.ports.clock import Clock
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.entities.pipacoin_wallet import PipaCoinWallet
from src.domain.entities.user import User
from src.domain.exceptions import SelfInteraction
from src.domain.value_objects.pipacoin_transaction_kind import (
    PipaCoinTransactionKind,
)
from src.domain.value_objects.telegram_ids import TelegramUserId


class TransferPipaCoinUseCase:
    """Transfers PipaCoin from the actor's global wallet to the target's."""

    def __init__(self, uow: UnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    async def execute(
        self, command: TransferPipaCoinCommand
    ) -> TransferPipaCoinResult:
        if command.actor_tg_id == command.target_tg_id:
            raise SelfInteraction()
        if command.amount <= 0:
            raise ValueError("amount must be positive")

        now = self._clock.now()
        async with self._uow as uow:
            actor = await _get_or_create_user(
                uow, command.actor_tg_id, command.actor_username, now
            )
            target = await _get_or_create_user(
                uow, command.target_tg_id, command.target_username, now
            )
            assert actor.id is not None and target.id is not None

            actor_wallet = await _get_or_create_wallet(uow, actor.id, now)
            target_wallet = await _get_or_create_wallet(uow, target.id, now)

            actor_wallet.debit(command.amount, now)
            target_wallet.credit(command.amount, now)
            await uow.pipacoin_wallets.update(actor_wallet)
            await uow.pipacoin_wallets.update(target_wallet)

            await pipacoin_ledger.record(
                uow,
                user_id=actor.id,
                delta=-command.amount,
                balance_after=actor_wallet.balance,
                kind=PipaCoinTransactionKind.TRANSFER_SENT,
                counterparty_user_id=target.id,
                now=now,
            )
            await pipacoin_ledger.record(
                uow,
                user_id=target.id,
                delta=command.amount,
                balance_after=target_wallet.balance,
                kind=PipaCoinTransactionKind.TRANSFER_RECEIVED,
                counterparty_user_id=actor.id,
                now=now,
            )

            await uow.commit()
            return TransferPipaCoinResult(
                amount=command.amount,
                actor_new_balance=actor_wallet.balance,
                target_new_balance=target_wallet.balance,
            )


async def _get_or_create_user(
    uow: UnitOfWork, tg_id: TelegramUserId, username: str | None, now: datetime
) -> User:
    existing = await uow.users.get_by_tg_id(tg_id)
    if existing is not None:
        return existing
    return await uow.users.add(User.new(tg_id, username, now))


async def _get_or_create_wallet(
    uow: UnitOfWork, user_id: int, now: datetime
) -> PipaCoinWallet:
    existing = await uow.pipacoin_wallets.get(user_id)
    if existing is not None:
        return existing
    return await uow.pipacoin_wallets.add(PipaCoinWallet.initial(user_id, now))
