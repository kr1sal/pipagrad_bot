from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.pipacoin_wallet import PipaCoinWallet
from src.infrastructure.persistence.models import PipaCoinWalletModel


class SqlAlchemyPipaCoinWalletRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_id: int) -> PipaCoinWallet | None:
        stmt = select(PipaCoinWalletModel).where(
            PipaCoinWalletModel.user_id == user_id
        )
        row = await self._session.scalar(stmt)
        return _to_entity(row) if row else None

    async def add(self, wallet: PipaCoinWallet) -> PipaCoinWallet:
        model = PipaCoinWalletModel(
            user_id=wallet.user_id,
            balance=wallet.balance,
            updated_at=wallet.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        wallet.id = model.id
        return wallet

    async def update(self, wallet: PipaCoinWallet) -> None:
        assert wallet.id is not None
        stmt = (
            update(PipaCoinWalletModel)
            .where(PipaCoinWalletModel.id == wallet.id)
            .values(balance=wallet.balance, updated_at=wallet.updated_at)
        )
        await self._session.execute(stmt)


def _to_entity(model: PipaCoinWalletModel) -> PipaCoinWallet:
    return PipaCoinWallet(
        id=model.id,
        user_id=model.user_id,
        balance=model.balance,
        updated_at=model.updated_at,
    )
