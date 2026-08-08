from __future__ import annotations

from src.application.dto.dick_history import DickHistoryLine, DickHistoryPage
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId

PAGE_SIZE = 10


class GetDickHistoryUseCase:
    """
    Read-only, newest-first page of a player's dick-size change log in one
    scope. `page` is 0-indexed. Fetches one extra row to detect whether a
    next page exists, without a separate count query.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def execute(
        self, tg_id: TelegramUserId, chat_id: TelegramChatId, page: int = 0
    ) -> DickHistoryPage:
        page = max(page, 0)
        async with self._uow as uow:
            user = await uow.users.get_by_tg_id(tg_id)
            if user is None or user.id is None:
                return DickHistoryPage(lines=[], page=page, has_prev=False, has_next=False)

            rows = await uow.dick_history.list_page(
                user.id, chat_id, limit=PAGE_SIZE + 1, offset=page * PAGE_SIZE
            )

        has_next = len(rows) > PAGE_SIZE
        lines = [
            DickHistoryLine(
                delta_cm=r.delta_cm,
                new_size_cm=r.new_size_cm,
                reason=r.reason,
                created_at=r.created_at,
            )
            for r in rows[:PAGE_SIZE]
        ]
        return DickHistoryPage(
            lines=lines, page=page, has_prev=page > 0, has_next=has_next
        )
