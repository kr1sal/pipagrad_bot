from __future__ import annotations

from src.application.dto.pipacoin import PipaCoinHistoryLine, PipaCoinHistoryPage
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.telegram_ids import TelegramUserId

PAGE_SIZE = 10


class GetPipaCoinHistoryUseCase:
    """
    Read-only, newest-first page of a player's PipaCoin ledger. `page` is
    0-indexed. Fetches one extra row to detect whether a next page exists,
    without a separate count query.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def execute(
        self, tg_id: TelegramUserId, page: int = 0
    ) -> PipaCoinHistoryPage:
        page = max(page, 0)
        async with self._uow as uow:
            user = await uow.users.get_by_tg_id(tg_id)
            if user is None or user.id is None:
                return PipaCoinHistoryPage(
                    lines=[], page=page, has_prev=False, has_next=False
                )

            rows = await uow.pipacoin_transactions.list_page(
                user.id, limit=PAGE_SIZE + 1, offset=page * PAGE_SIZE
            )
            has_next = len(rows) > PAGE_SIZE
            rows = rows[:PAGE_SIZE]

            lines: list[PipaCoinHistoryLine] = []
            for r in rows:
                counterparty_label = None
                if r.counterparty_user_id is not None:
                    counterparty = await uow.users.get_by_id(r.counterparty_user_id)
                    counterparty_label = (
                        counterparty.username or f"id{int(counterparty.tg_id)}"
                        if counterparty is not None
                        else None
                    )
                lines.append(
                    PipaCoinHistoryLine(
                        delta=r.delta,
                        balance_after=r.balance_after,
                        kind=r.kind,
                        counterparty_label=counterparty_label,
                        created_at=r.created_at,
                    )
                )

        return PipaCoinHistoryPage(
            lines=lines, page=page, has_prev=page > 0, has_next=has_next
        )
