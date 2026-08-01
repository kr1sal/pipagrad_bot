from __future__ import annotations

from datetime import timedelta

from aiogram import Bot
from dishka import Provider, Scope, from_context, make_async_container, provide
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.application.ports.clock import Clock
from src.application.ports.randomizer import Randomizer
from src.application.ports.telegram_gateway import TelegramGateway
from src.application.ports.unit_of_work import UnitOfWork
from src.application.use_cases.challenge_battle import ChallengeBattleUseCase
from src.application.use_cases.ensure_group_registered import (
    EnsureGroupRegisteredUseCase,
)
from src.application.use_cases.get_global_top import GetGlobalTopUseCase
from src.application.use_cases.get_group_settings import GetGroupSettingsUseCase
from src.application.use_cases.get_my_chat_balance import GetMyChatBalanceUseCase
from src.application.use_cases.get_my_preferences import GetMyPreferencesUseCase
from src.application.use_cases.get_user_global_stats import GetUserGlobalStatsUseCase
from src.application.use_cases.grow_dick import GrowDickConfig, GrowDickUseCase
from src.application.use_cases.join_pending import (
    JoinBotBattleUseCase,
    JoinOrgyUseCase,
)
from src.application.use_cases.perform_interaction import PerformInteractionUseCase
from src.application.use_cases.resolve_pending_events import (
    ResolvePendingEventsUseCase,
)
from src.application.use_cases.respond_to_battle import RespondToBattleUseCase
from src.application.use_cases.toggle_my_preference import ToggleMyPreferenceUseCase
from src.application.use_cases.trigger_random_events import (
    TriggerRandomEventsCycleUseCase,
)
from src.application.use_cases.update_group_settings import UpdateGroupSettingsUseCase
from src.domain.entities.semen_balance import SemenConfig
from src.infrastructure.config.settings import Settings
from src.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from src.infrastructure.system.clock import SystemClock
from src.infrastructure.system.randomizer import SystemRandomizer
from src.infrastructure.telegram.aiogram_gateway import AiogramTelegramGateway


class AppProvider(Provider):
    scope = Scope.APP

    settings = from_context(provides=Settings, scope=Scope.APP)
    bot = from_context(provides=Bot, scope=Scope.APP)

    @provide
    def clock(self) -> Clock:
        return SystemClock()

    @provide
    def randomizer(self) -> Randomizer:
        return SystemRandomizer()

    @provide
    def telegram_gateway(self, bot: Bot) -> TelegramGateway:
        return AiogramTelegramGateway(bot)

    @provide
    def grow_config(self, settings: Settings) -> GrowDickConfig:
        return GrowDickConfig(
            cooldown=timedelta(hours=settings.grow_cooldown_hours),
            min_delta_cm=settings.grow_min_delta_cm,
            max_delta_cm=settings.grow_max_delta_cm,
        )

    @provide
    def semen_config(self, settings: Settings) -> SemenConfig:
        return SemenConfig(
            base_cap_ml=settings.semen_base_cap_ml,
            cap_per_cm=settings.semen_cap_per_cm,
            regen_per_hour=settings.semen_regen_per_hour,
            fuck_cost_ml=settings.fuck_cost_ml,
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

    @provide
    def ensure_group_registered(
        self, uow: UnitOfWork, clock: Clock
    ) -> EnsureGroupRegisteredUseCase:
        return EnsureGroupRegisteredUseCase(uow, clock)

    @provide
    def get_group_settings(
        self, uow: UnitOfWork, clock: Clock
    ) -> GetGroupSettingsUseCase:
        return GetGroupSettingsUseCase(uow, clock)

    @provide
    def update_group_settings(
        self,
        uow: UnitOfWork,
        clock: Clock,
        telegram: TelegramGateway,
    ) -> UpdateGroupSettingsUseCase:
        return UpdateGroupSettingsUseCase(uow, clock, telegram)

    @provide
    def perform_interaction(
        self, uow: UnitOfWork, clock: Clock, semen_config: SemenConfig
    ) -> PerformInteractionUseCase:
        return PerformInteractionUseCase(uow, clock, semen_config)

    @provide
    def get_my_preferences(
        self, uow: UnitOfWork, clock: Clock
    ) -> GetMyPreferencesUseCase:
        return GetMyPreferencesUseCase(uow, clock)

    @provide
    def toggle_my_preference(
        self, uow: UnitOfWork, clock: Clock
    ) -> ToggleMyPreferenceUseCase:
        return ToggleMyPreferenceUseCase(uow, clock)

    @provide
    def challenge_battle(
        self, uow: UnitOfWork, clock: Clock
    ) -> ChallengeBattleUseCase:
        return ChallengeBattleUseCase(uow, clock)

    @provide
    def respond_to_battle(
        self, uow: UnitOfWork, clock: Clock, randomizer: Randomizer
    ) -> RespondToBattleUseCase:
        return RespondToBattleUseCase(uow, clock, randomizer)

    @provide
    def trigger_random_events(
        self,
        uow: UnitOfWork,
        clock: Clock,
        randomizer: Randomizer,
        telegram: TelegramGateway,
        semen_config: SemenConfig,
    ) -> TriggerRandomEventsCycleUseCase:
        return TriggerRandomEventsCycleUseCase(
            uow, clock, randomizer, telegram, semen_config
        )

    @provide
    def resolve_pending_events(
        self,
        uow: UnitOfWork,
        clock: Clock,
        randomizer: Randomizer,
        telegram: TelegramGateway,
        semen_config: SemenConfig,
    ) -> ResolvePendingEventsUseCase:
        return ResolvePendingEventsUseCase(
            uow, clock, randomizer, telegram, semen_config
        )

    @provide
    def join_orgy(self, uow: UnitOfWork, clock: Clock) -> JoinOrgyUseCase:
        return JoinOrgyUseCase(uow, clock)

    @provide
    def join_bot_battle(
        self, uow: UnitOfWork, clock: Clock
    ) -> JoinBotBattleUseCase:
        return JoinBotBattleUseCase(uow, clock)

    @provide
    def get_global_top(self, uow: UnitOfWork) -> GetGlobalTopUseCase:
        return GetGlobalTopUseCase(uow)

    @provide
    def get_user_global_stats(self, uow: UnitOfWork) -> GetUserGlobalStatsUseCase:
        return GetUserGlobalStatsUseCase(uow)

    @provide
    def get_my_chat_balance(
        self, uow: UnitOfWork, clock: Clock, semen_config: SemenConfig
    ) -> GetMyChatBalanceUseCase:
        return GetMyChatBalanceUseCase(uow, clock, semen_config)


def build_container(settings: Settings, bot: Bot):
    return make_async_container(
        AppProvider(),
        RequestProvider(),
        context={Settings: settings, Bot: bot},
    )
