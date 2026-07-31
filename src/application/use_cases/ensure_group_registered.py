from __future__ import annotations

from src.application.dto.group_settings import EnsureGroupRegisteredCommand
from src.application.ports.clock import Clock
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.entities.group import Group


class EnsureGroupRegisteredUseCase:
    def __init__(self, uow: UnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    async def execute(self, command: EnsureGroupRegisteredCommand) -> Group:
        async with self._uow as uow:
            existing = await uow.groups.get(command.chat_id)
            if existing is not None:
                return existing
            group = Group.new(
                chat_id=command.chat_id,
                title=command.title,
                added_by_tg_id=command.added_by_tg_id,
                now=self._clock.now(),
            )
            saved = await uow.groups.add(group)
            await uow.commit()
            return saved
