from __future__ import annotations

from src.application.dto.stats import UserGlobalStats
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.telegram_ids import TelegramUserId


class GetUserGlobalStatsUseCase:
    """
    Aggregates one user's dick stats across all chats they've played in.
    Returns None if the user has never grown anywhere — the caller decides
    what to render for a fresh player.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def execute(self, tg_id: TelegramUserId) -> UserGlobalStats | None:
        async with self._uow as uow:
            user = await uow.users.get_by_tg_id(tg_id)
            if user is None or user.id is None:
                return None
            dicks = await uow.dicks.list_all_for_user(user.id)
            if not dicks:
                return None
            sizes = [d.size.cm for d in dicks]
            return UserGlobalStats(
                chats_count=len(dicks),
                total_cm=sum(sizes),
                max_cm=max(sizes),
            )
