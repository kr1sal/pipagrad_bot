from __future__ import annotations

from datetime import timedelta

from dishka import Provider, Scope, from_context, make_async_container, provide
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.application.ports.clock import Clock
from src.application.ports.randomizer import Randomizer
from src.application.ports.unit_of_work import UnitOfWork
from src.application.use_cases.grow_dick import GrowDickConfig, GrowDickUseCase
from src.infrastructure.config.settings import Settings
from src.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from src.infrastructure.system.clock import SystemClock
from src.infrastructure.system.randomizer import SystemRandomizer


class AppProvider(Provider):
    scope = Scope.APP

    settings = from_context(provides=Settings, scope=Scope.APP)

    @provide
    def clock(self) -> Clock:
        return SystemClock()

    @provide
    def randomizer(self) -> Randomizer:
        return SystemRandomizer()

    @provide
    def grow_config(self, settings: Settings) -> GrowDickConfig:
        return GrowDickConfig(
            cooldown=timedelta(hours=settings.grow_cooldown_hours),
            min_delta_cm=settings.grow_min_delta_cm,
            max_delta_cm=settings.grow_max_delta_cm,
        )

    @provide
    async def engine(self, settings: Settings) -> AsyncEngine:
        return create_async_engine(settings.postgres_dsn, pool_pre_ping=True)

    @provide
    def session_factory(
        self, engine: AsyncEngine
    ) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(engine, expire_on_commit=False)


class RequestProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def uow(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> UnitOfWork:
        return SqlAlchemyUnitOfWork(session_factory)

    @provide
    def grow_dick_use_case(
        self,
        uow: UnitOfWork,
        clock: Clock,
        randomizer: Randomizer,
        config: GrowDickConfig,
    ) -> GrowDickUseCase:
        return GrowDickUseCase(uow, clock, randomizer, config)


def build_container(settings: Settings):
    return make_async_container(
        AppProvider(),
        RequestProvider(),
        context={Settings: settings},
    )
