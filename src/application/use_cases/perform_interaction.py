from __future__ import annotations

from src.application.dto.interaction import (
    InteractionDenied,
    InteractionPerformed,
    PerformInteractionCommand,
)
from src.application.ports.clock import Clock
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.entities.group import Group
from src.domain.entities.semen_balance import SemenBalance, SemenConfig
from src.domain.entities.user import User
from src.domain.exceptions import SelfInteraction
from src.domain.services.interaction_policy import Denial, check as check_interaction
from src.domain.value_objects.interaction_type import InteractionType
from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId
from src.domain.value_objects.user_preferences import UserPreferences


class PerformInteractionUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        semen_config: SemenConfig,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._semen_config = semen_config

    async def execute(
        self, command: PerformInteractionCommand
    ) -> InteractionPerformed | InteractionDenied:
        if command.actor_tg_id == command.target_tg_id:
            raise SelfInteraction()

        now = self._clock.now()
        async with self._uow as uow:
            group = await _get_or_create_group(uow, command.chat_id, now)
            actor = await _get_or_create_user(
                uow, command.actor_tg_id, command.actor_username, now
            )
            target = await _get_or_create_user(
                uow, command.target_tg_id, command.target_username, now
            )
            assert actor.id is not None and target.id is not None

            target_prefs = await uow.user_preferences.get(target.id, command.chat_id)
            if target_prefs is None:
                target_prefs = UserPreferences.default()

            denial = check_interaction(command.kind, group.settings, target_prefs)
            if denial is not None:
                return InteractionDenied(kind=command.kind, reason=denial)

            if command.kind is InteractionType.FUCK:
                semen_denial = await self._spend_semen_or_deny(
                    uow, actor.id, target.id, command.chat_id, now
                )
                if semen_denial is not None:
                    return semen_denial

            await uow.commit()
            return InteractionPerformed(
                kind=command.kind,
                actor_tg_id=command.actor_tg_id,
                target_tg_id=command.target_tg_id,
            )

    async def _spend_semen_or_deny(
        self,
        uow: UnitOfWork,
        actor_id: int,
        target_id: int,
        chat_id: TelegramChatId,
        now,
    ) -> InteractionDenied | None:
        cfg = self._semen_config
        actor_cap = cfg.cap_for(await _dick_size(uow, actor_id, chat_id))
        target_cap = cfg.cap_for(await _dick_size(uow, target_id, chat_id))

        actor_bal = await self._load_balance(uow, actor_id, chat_id, now, actor_cap)
        target_bal = await self._load_balance(
            uow, target_id, chat_id, now, target_cap
        )

        actor_current = actor_bal.current_ml(now, cfg.regen_per_hour, actor_cap)
        target_current = target_bal.current_ml(now, cfg.regen_per_hour, target_cap)

        if actor_current < cfg.fuck_cost_ml:
            return InteractionDenied(
                kind=InteractionType.FUCK,
                reason=Denial.ACTOR_NO_SEMEN,
                current_ml=actor_current,
                cost_ml=cfg.fuck_cost_ml,
            )
        if target_current < cfg.fuck_cost_ml:
            return InteractionDenied(
                kind=InteractionType.FUCK,
                reason=Denial.TARGET_NO_SEMEN,
                current_ml=target_current,
                cost_ml=cfg.fuck_cost_ml,
            )

        actor_bal.try_spend(cfg.fuck_cost_ml, now, cfg.regen_per_hour, actor_cap)
        target_bal.try_spend(cfg.fuck_cost_ml, now, cfg.regen_per_hour, target_cap)
        await uow.semen.upsert(actor_bal)
        await uow.semen.upsert(target_bal)
        return None

    async def _load_balance(
        self,
        uow: UnitOfWork,
        user_id: int,
        chat_id: TelegramChatId,
        now,
        initial_cap_ml: int,
    ) -> SemenBalance:
        existing = await uow.semen.get(user_id, chat_id)
        if existing is not None:
            return existing
        # Fresh players start at their current cap so first-timers can act.
        return SemenBalance.initial(user_id, chat_id, initial_cap_ml, now)


async def _dick_size(
    uow: UnitOfWork, user_id: int, chat_id: TelegramChatId
) -> int:
    dick = await uow.dicks.get(user_id, chat_id)
    return dick.size.cm if dick is not None else 0


async def _get_or_create_group(
    uow: UnitOfWork, chat_id: TelegramChatId, now
) -> Group:
    existing = await uow.groups.get(chat_id)
    if existing is not None:
        return existing
    group = Group.new(
        chat_id=chat_id, title=None, added_by_tg_id=None, now=now
    )
    return await uow.groups.add(group)


async def _get_or_create_user(
    uow: UnitOfWork,
    tg_id: TelegramUserId,
    username: str | None,
    now,
) -> User:
    existing = await uow.users.get_by_tg_id(tg_id)
    if existing is not None:
        return existing
    return await uow.users.add(User.new(tg_id, username, now))
