from __future__ import annotations

from src.application.dto.stats import TopEntry
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId


class GetTopUseCase:
    """
    Leaderboard for one scope: ranks players by dick size within the given
    chat_id — a real chat for a local leaderboard, or GLOBAL_CHAT_ID for the
    global one shared by DMs and inline mode.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def execute(
        self, chat_id: TelegramChatId, limit: int = 10
    ) -> list[TopEntry]:
        async with self._uow as uow:
            dicks = await uow.dicks.list_top_for_chat(chat_id, limit)
            entries: list[TopEntry] = []
            for rank, dick in enumerate(dicks, start=1):
                user = await uow.users.get_by_id(dick.user_id)
                if user is None:
                    continue
                entries.append(
                    TopEntry(
                        rank=rank,
                        tg_id=TelegramUserId(user.tg_id),
                        username=user.username,
                        size_cm=dick.size.cm,
                    )
                )
            return entries
