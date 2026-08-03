from __future__ import annotations

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.battle import Battle, BattleStatus
from src.domain.value_objects.telegram_ids import TelegramChatId
from src.infrastructure.persistence.models import BattleModel

_ACTIVE_STATUSES = (BattleStatus.PENDING.value, BattleStatus.OPEN.value)


class SqlAlchemyBattleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, battle: Battle) -> Battle:
        model = BattleModel(
            chat_id=int(battle.chat_id),
            challenger_user_id=battle.challenger_user_id,
            opponent_user_id=battle.opponent_user_id,
            stake_cm=battle.stake_cm,
            status=battle.status.value,
            winner_user_id=battle.winner_user_id,
            created_at=battle.created_at,
            resolved_at=battle.resolved_at,
        )
        self._session.add(model)
        await self._session.flush()
        battle.id = model.id
        return battle

    async def get(self, battle_id: int) -> Battle | None:
        row = await self._session.get(BattleModel, battle_id)
        return _to_entity(row) if row else None

    async def get_active_between(
        self, chat_id: TelegramChatId, user_a_id: int, user_b_id: int
    ) -> Battle | None:
        stmt = (
            select(BattleModel)
            .where(
                BattleModel.chat_id == int(chat_id),
                BattleModel.status.in_(_ACTIVE_STATUSES),
                or_(
                    and_(
                        BattleModel.challenger_user_id == user_a_id,
                        BattleModel.opponent_user_id == user_b_id,
                    ),
                    and_(
                        BattleModel.challenger_user_id == user_b_id,
                        BattleModel.opponent_user_id == user_a_id,
                    ),
                ),
            )
            .limit(1)
        )
        row = (await self._session.scalars(stmt)).first()
        return _to_entity(row) if row else None

    async def update(self, battle: Battle) -> None:
        assert battle.id is not None
        stmt = (
            update(BattleModel)
            .where(BattleModel.id == battle.id)
            .values(
                status=battle.status.value,
                winner_user_id=battle.winner_user_id,
                resolved_at=battle.resolved_at,
            )
        )
        await self._session.execute(stmt)


def _to_entity(model: BattleModel) -> Battle:
    return Battle(
        id=model.id,
        chat_id=TelegramChatId(model.chat_id),
        challenger_user_id=model.challenger_user_id,
        opponent_user_id=model.opponent_user_id,
        stake_cm=model.stake_cm,
        status=BattleStatus(model.status),
        winner_user_id=model.winner_user_id,
        created_at=model.created_at,
        resolved_at=model.resolved_at,
    )
