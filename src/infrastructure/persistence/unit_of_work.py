from __future__ import annotations

from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.infrastructure.persistence.repositories.dick_repository import (
    SqlAlchemyDickRepository,
)
from src.infrastructure.persistence.repositories.group_repository import (
    SqlAlchemyGroupRepository,
)
from src.infrastructure.persistence.repositories.user_repository import (
    SqlAlchemyUserRepository,
)


class SqlAlchemyUnitOfWork:
    users: SqlAlchemyUserRepository
    dicks: SqlAlchemyDickRepository
    groups: SqlAlchemyGroupRepository

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        self.users = SqlAlchemyUserRepository(self._session)
        self.dicks = SqlAlchemyDickRepository(self._session)
        self.groups = SqlAlchemyGroupRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        assert self._session is not None
        try:
            if exc is not None:
                await self._session.rollback()
        finally:
            await self._session.close()
            self._session = None

    async def commit(self) -> None:
        assert self._session is not None
        await self._session.commit()

    async def rollback(self) -> None:
        assert self._session is not None
        await self._session.rollback()
