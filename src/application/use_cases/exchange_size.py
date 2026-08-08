from __future__ import annotations

from dataclasses import dataclass

from src.application import dick_history, pipacoin_ledger
from src.application.dto.pipacoin import ExchangeSizeCommand, ExchangeSizeResult
from src.application.ports.clock import Clock
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.entities.pipacoin_wallet import PipaCoinWallet
from src.domain.entities.user import User
from src.domain.exceptions import InsufficientDickSize
from src.domain.value_objects.dick_history_reason import DickHistoryReason
from src.domain.value_objects.pipacoin_transaction_kind import (
    PipaCoinTransactionKind,
)


@dataclass(frozen=True, slots=True)
class ExchangeSizeConfig:
    pipacoin_per_cm: int


class ExchangeSizeUseCase:
    """Burns dick-size cm in one chat, mints PipaCoin into the global wallet."""

    def __init__(self, uow: UnitOfWork, clock: Clock, config: ExchangeSizeConfig) -> None:
        self._uow = uow
        self._clock = clock
        self._config = config

    async def execute(self, command: ExchangeSizeCommand) -> ExchangeSizeResult:
        if command.amount_cm <= 0:
            raise ValueError("amount must be positive")

        now = self._clock.now()
        async with self._uow as uow:
            user = await uow.users.get_by_tg_id(command.tg_user_id)
            if user is None:
                user = await uow.users.add(
                    User.new(command.tg_user_id, command.tg_username, now)
                )
            assert user.id is not None

            dick = await uow.dicks.get(user.id, command.chat_id)
            actual_cm = dick.size.cm if dick is not None else 0
            if dick is None or actual_cm < command.amount_cm:
                raise InsufficientDickSize(needed=command.amount_cm, actual=actual_cm)

            dick.size = dick.size.apply(-command.amount_cm)
            await uow.dicks.update(dick)
            await dick_history.record(
                uow,
                user_id=user.id,
                chat_id=command.chat_id,
                delta_cm=-command.amount_cm,
                new_size_cm=dick.size.cm,
                reason=DickHistoryReason.EXCHANGE,
                now=now,
            )

            wallet = await uow.pipacoin_wallets.get(user.id)
            if wallet is None:
                wallet = await uow.pipacoin_wallets.add(
                    PipaCoinWallet.initial(user.id, now)
                )
            gained = command.amount_cm * self._config.pipacoin_per_cm
            wallet.credit(gained, now)
            await uow.pipacoin_wallets.update(wallet)
            await pipacoin_ledger.record(
                uow,
                user_id=user.id,
                delta=gained,
                balance_after=wallet.balance,
                kind=PipaCoinTransactionKind.EXCHANGE,
                counterparty_user_id=None,
                now=now,
            )

            await uow.commit()
            return ExchangeSizeResult(
                spent_cm=command.amount_cm,
                gained_pipacoin=gained,
                new_size_cm=dick.size.cm,
                new_balance=wallet.balance,
            )
