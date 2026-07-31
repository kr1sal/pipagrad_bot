from __future__ import annotations

from src.application.dto.interaction import (
    InteractionDenied,
    InteractionPerformed,
    PerformInteractionCommand,
)
from src.application.ports.clock import Clock
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.entities.group import Group
from src.domain.entities.user import User
from src.domain.exceptions import SelfInteraction
from src.domain.services.interaction_policy import check as check_interaction
from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId
from src.domain.value_objects.user_preferences import UserPreferences


class PerformInteractionUseCase:
    def __init__(self, uow: UnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    async def execute(
        self, command: PerformInteractionCommand
    ) -> InteractionPerformed | InteractionDenied:
        if command.actor_tg_id == command.target_tg_id:
            raise SelfInteraction()

        now = self._clock.now()
        async with self._uow as uow:
            group = await _get_or_create_group(uow, command.chat_id, now)
            target = await _get_or_create_user(
                uow, command.target_tg_id, command.target_username, now
            )
            # Ensure actor exists too (for future analytics), don't fail if not
            await _get_or_create_user(
                uow, command.actor_tg_id, command.actor_username, now
            )
            assert target.id is not None

            target_prefs = await uow.user_preferences.get(target.id, command.chat_id)
            if target_prefs is None:
                target_prefs = UserPreferences.default()

            denial = check_interaction(command.kind, group.settings, target_prefs)
            if denial is not None:
                return InteractionDenied(kind=command.kind, reason=denial)

            await uow.commit()
            return InteractionPerformed(
                kind=command.kind,
                actor_tg_id=command.actor_tg_id,
                target_tg_id=command.target_tg_id,
            )


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
