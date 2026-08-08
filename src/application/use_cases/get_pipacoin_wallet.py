from __future__ import annotations

from src.application.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.telegram_ids import TelegramUserId


class GetPipaCoinWalletUseCase:
    """Read-only balance lookup. Players who haven't exchanged yet just have 0."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def execute(self, tg_id: TelegramUserId) -> int:
        async with self._uow as uow:
            user = await uow.users.get_by_tg_id(tg_id)
            if user is None or user.id is None:
                return 0
            wallet = await uow.pipacoin_wallets.get(user.id)
            return wallet.balance if wallet is not None else 0
