from __future__ import annotations

from src.application.dto.stats import TopEntry
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.telegram_ids import TelegramUserId


class GetGlobalTopUseCase:
    """
    Global leaderboard: ranks players by the maximum size of their dick across
    all chats. A player is represented once even if they play in many chats.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def execute(self, limit: int = 10) -> list[TopEntry]:
        async with self._uow as uow:
            pairs = await uow.dicks.list_global_top_by_max(limit)
            entries: list[TopEntry] = []
            for rank, (user_id, max_cm) in enumerate(pairs, start=1):
                user = await uow.users.get_by_id(user_id)
                if user is None:
                    continue
                entries.append(
                    TopEntry(
                        rank=rank,
                        tg_id=TelegramUserId(user.tg_id),
                        username=user.username,
                        size_cm=max_cm,
                    )
                )
            return entries
