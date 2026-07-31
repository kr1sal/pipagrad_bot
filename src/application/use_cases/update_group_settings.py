from __future__ import annotations

from src.application.dto.group_settings import (
    SetRandomEventInterval,
    ToggleBattles,
    ToggleInteraction,
    ToggleRandomEvents,
    UpdateGroupSettingsCommand,
)
from src.application.ports.clock import Clock
from src.application.ports.telegram_gateway import TelegramGateway
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.entities.group import Group, GroupSettings
from src.domain.exceptions import NotAnAdmin


class UpdateGroupSettingsUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        telegram: TelegramGateway,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._telegram = telegram

    async def execute(self, command: UpdateGroupSettingsCommand) -> Group:
        is_admin = await self._telegram.is_chat_admin(
            command.chat_id, command.actor_tg_id
        )
        if not is_admin:
            raise NotAnAdmin()

        async with self._uow as uow:
            group = await uow.groups.get(command.chat_id)
            if group is None:
                group = Group.new(
                    chat_id=command.chat_id,
                    title=None,
                    added_by_tg_id=None,
                    now=self._clock.now(),
                )
                group = await uow.groups.add(group)

            group.settings = _apply(group.settings, command)
            await uow.groups.update_settings(group.chat_id, group.settings)
            await uow.commit()
            return group


def _apply(settings: GroupSettings, command: UpdateGroupSettingsCommand) -> GroupSettings:
    change = command.change
    match change:
        case ToggleBattles():
            return settings.toggled_battles()
        case ToggleRandomEvents():
            return settings.toggled_random_events()
        case ToggleInteraction(kind=kind):
            return settings.toggled_interaction(kind)
        case SetRandomEventInterval(minutes=m):
            return settings.with_random_event_interval(m)
        case _:  # pragma: no cover
            raise TypeError(f"Unknown settings change: {change!r}")
