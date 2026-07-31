from __future__ import annotations

from src.application.ports.clock import Clock
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.entities.group import Group
from src.domain.value_objects.telegram_ids import TelegramChatId


class GetGroupSettingsUseCase:
    """
    Returns the group with its settings. Auto-registers the group with defaults if
    it doesn't exist yet — this handles the case where the bot was already in the
    chat before we started tracking chat-member events.
    """

    def __init__(self, uow: UnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    async def execute(self, chat_id: TelegramChatId) -> Group:
        async with self._uow as uow:
            existing = await uow.groups.get(chat_id)
            if existing is not None:
                return existing
            group = Group.new(
                chat_id=chat_id,
                title=None,
                added_by_tg_id=None,
                now=self._clock.now(),
            )
            saved = await uow.groups.add(group)
            await uow.commit()
            return saved
