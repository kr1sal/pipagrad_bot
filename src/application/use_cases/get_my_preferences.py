from __future__ import annotations

from src.application.dto.interaction import GetMyPreferencesCommand
from src.application.ports.clock import Clock
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.entities.user import User
from src.domain.value_objects.user_preferences import UserPreferences


class GetMyPreferencesUseCase:
    def __init__(self, uow: UnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    async def execute(self, command: GetMyPreferencesCommand) -> UserPreferences:
        now = self._clock.now()
        async with self._uow as uow:
            user = await uow.users.get_by_tg_id(command.tg_user_id)
            if user is None:
                user = await uow.users.add(
                    User.new(command.tg_user_id, command.tg_username, now)
                )
                await uow.commit()
            assert user.id is not None

            prefs = await uow.user_preferences.get(user.id, command.chat_id)
            return prefs if prefs is not None else UserPreferences.default()
