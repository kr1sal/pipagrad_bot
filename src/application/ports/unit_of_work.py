from __future__ import annotations

from types import TracebackType
from typing import Protocol, Self

from src.application.ports.repositories import (
    BattleRepository,
    DickHistoryRepository,
    DickRepository,
    GroupRepository,
    PendingEventRepository,
    PipaCoinTransactionRepository,
    PipaCoinWalletRepository,
    SemenBalanceRepository,
    UserPreferencesRepository,
    UserRepository,
)


class UnitOfWork(Protocol):
    users: UserRepository
    dicks: DickRepository
    dick_history: DickHistoryRepository
    groups: GroupRepository
    user_preferences: UserPreferencesRepository
    battles: BattleRepository
    semen: SemenBalanceRepository
    pending_events: PendingEventRepository
    pipacoin_wallets: PipaCoinWalletRepository
    pipacoin_transactions: PipaCoinTransactionRepository

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
