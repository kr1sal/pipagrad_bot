from __future__ import annotations

from src.application.dto.stats import MyChatBalance
from src.application.ports.clock import Clock
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.entities.semen_balance import SemenConfig
from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId


class GetMyChatBalanceUseCase:
    """
    Read-only projection of the caller's per-chat state: current dick size and
    semen level. No mutation — safe to call for display purposes without
    creating rows for players who haven't started yet (returns fresh defaults).
    """

    def __init__(
        self, uow: UnitOfWork, clock: Clock, semen_config: SemenConfig
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._cfg = semen_config

    async def execute(
        self, tg_id: TelegramUserId, chat_id: TelegramChatId
    ) -> MyChatBalance:
        now = self._clock.now()
        async with self._uow as uow:
            user = await uow.users.get_by_tg_id(tg_id)

            size_cm = 0
            current_ml = self._cfg.base_cap_ml
            if user is not None and user.id is not None:
                dick = await uow.dicks.get(user.id, chat_id)
                if dick is not None:
                    size_cm = dick.size.cm
                cap_ml = self._cfg.cap_for(size_cm)
                balance = await uow.semen.get(user.id, chat_id)
                if balance is not None:
                    current_ml = balance.current_ml(
                        now, self._cfg.regen_per_hour, cap_ml
                    )
                else:
                    # fresh players start at cap
                    current_ml = cap_ml

        cap_ml = self._cfg.cap_for(size_cm)
        return MyChatBalance(
            dick_size_cm=size_cm,
            semen_current_ml=current_ml,
            semen_cap_ml=cap_ml,
            regen_per_hour=self._cfg.regen_per_hour,
        )
