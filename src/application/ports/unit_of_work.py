from __future__ import annotations

from types import TracebackType
from typing import Protocol, Self

from src.application.ports.repositories import DickRepository, UserRepository


class UnitOfWork(Protocol):
    users: UserRepository
    dicks: DickRepository

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
