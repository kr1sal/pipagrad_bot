from __future__ import annotations

from src.application.dto.stats import ChatTopEntry
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId


class GetChatTopUseCase:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def execute(
        self, chat_id: TelegramChatId, limit: int = 10
    ) -> list[ChatTopEntry]:
        async with self._uow as uow:
            top_dicks = await uow.dicks.list_top_for_chat(chat_id, limit)
            entries: list[ChatTopEntry] = []
            for rank, dick in enumerate(top_dicks, start=1):
                user = await uow.users.get_by_id(dick.user_id)
                if user is None:
                    continue
                entries.append(
                    ChatTopEntry(
                        rank=rank,
                        tg_id=TelegramUserId(user.tg_id),
                        username=user.username,
                        size_cm=dick.size.cm,
                    )
                )
            return entries
