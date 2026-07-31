from __future__ import annotations

from src.application.dto.battle import (
    BattleDeclinedResult,
    BattleExpiredResult,
    BattleResolvedResult,
    RespondToBattleCommand,
)
from src.application.ports.clock import Clock
from src.application.ports.randomizer import Randomizer
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.entities.battle import BattleStatus
from src.domain.exceptions import (
    BattleNotFound,
    BattleNotPending,
    InsufficientDickSize,
    NotYourBattle,
)
from src.domain.services.battle_resolver import resolve
from src.domain.value_objects.telegram_ids import TelegramUserId


class RespondToBattleUseCase:
    def __init__(
        self, uow: UnitOfWork, clock: Clock, randomizer: Randomizer
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._randomizer = randomizer

    async def execute(
        self, command: RespondToBattleCommand
    ) -> BattleResolvedResult | BattleDeclinedResult | BattleExpiredResult:
        now = self._clock.now()
        async with self._uow as uow:
            battle = await uow.battles.get(command.battle_id)
            if battle is None:
                raise BattleNotFound()
            if battle.status is not BattleStatus.PENDING:
                raise BattleNotPending()

            opponent = await uow.users.get_by_tg_id(command.actor_tg_id)
            if opponent is None or opponent.id != battle.opponent_user_id:
                raise NotYourBattle()

            challenger = await uow.users.get_by_id(battle.challenger_user_id)
            assert challenger is not None

            if battle.is_expired(now):
                battle.expire(now)
                await uow.battles.update(battle)
                await uow.commit()
                return BattleExpiredResult()

            if not command.accept:
                battle.decline(now)
                await uow.battles.update(battle)
                await uow.commit()
                return BattleDeclinedResult(
                    challenger_tg_id=challenger.tg_id,
                    opponent_tg_id=opponent.tg_id,
                )

            challenger_dick = await uow.dicks.get(
                battle.challenger_user_id, battle.chat_id
            )
            opponent_dick = await uow.dicks.get(
                battle.opponent_user_id, battle.chat_id
            )
            assert challenger_dick is not None and opponent_dick is not None

            if challenger_dick.size.cm < battle.stake_cm:
                raise InsufficientDickSize(battle.stake_cm, challenger_dick.size.cm)
            if opponent_dick.size.cm < battle.stake_cm:
                raise InsufficientDickSize(battle.stake_cm, opponent_dick.size.cm)

            total = challenger_dick.size.cm + opponent_dick.size.cm
            roll = self._randomizer.int_between(1, total) if total > 0 else 0
            outcome = resolve(challenger_dick.size.cm, opponent_dick.size.cm, roll)

            if outcome.challenger_wins:
                winner_dick, loser_dick = challenger_dick, opponent_dick
                winner_user, loser_user = challenger, opponent
            else:
                winner_dick, loser_dick = opponent_dick, challenger_dick
                winner_user, loser_user = opponent, challenger

            winner_dick.size = winner_dick.size.apply(battle.stake_cm)
            loser_dick.size = loser_dick.size.apply(-battle.stake_cm)
            assert winner_user.id is not None
            battle.resolve(winner_user_id=winner_user.id, now=now)

            await uow.dicks.update(winner_dick)
            await uow.dicks.update(loser_dick)
            await uow.battles.update(battle)
            await uow.commit()

            return BattleResolvedResult(
                stake_cm=battle.stake_cm,
                winner_tg_id=winner_user.tg_id,
                loser_tg_id=loser_user.tg_id,
                winner_new_size_cm=winner_dick.size.cm,
                loser_new_size_cm=loser_dick.size.cm,
            )


