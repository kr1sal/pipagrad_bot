from __future__ import annotations

from types import TracebackType
from typing import Protocol, Self

from src.application.ports.repositories import (
    BattleRepository,
    DickRepository,
    GroupRepository,
    PendingEventRepository,
    SemenBalanceRepository,
    UserPreferencesRepository,
    UserRepository,
)


class UnitOfWork(Protocol):
    users: UserRepository
    dicks: DickRepository
    groups: GroupRepository
    user_preferences: UserPreferencesRepository
    battles: BattleRepository
    semen: SemenBalanceRepository
    pending_events: PendingEventRepository

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
