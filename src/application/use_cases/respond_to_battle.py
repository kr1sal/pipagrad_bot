from __future__ import annotations

from datetime import timedelta

from src.application.dto.battle import (
    BattleDeclinedResult,
    BattleExpiredResult,
    BattleOpenedResult,
    RespondToBattleCommand,
)
from src.application.ports.clock import Clock
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.entities.battle import BattleStatus
from src.domain.entities.pending_event import (
    TEAM_BATTLE_TIMER_MINUTES,
    PendingEvent,
    PendingEventKind,
)
from src.domain.exceptions import (
    BattleNotFound,
    BattleNotPending,
    InsufficientDickSize,
    NotYourBattle,
)


class RespondToBattleUseCase:
    def __init__(self, uow: UnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    async def execute(
        self, command: RespondToBattleCommand
    ) -> BattleOpenedResult | BattleDeclinedResult | BattleExpiredResult:
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

            battle.open_for_joining()
            await uow.battles.update(battle)

            challenger_label = challenger.username or f"id{int(challenger.tg_id)}"
            opponent_label = opponent.username or f"id{int(opponent.tg_id)}"

            assert battle.id is not None
            pending = PendingEvent.new(
                chat_id=battle.chat_id,
                kind=PendingEventKind.TEAM_BATTLE,
                chat_message_id=command.chat_message_id,
                resolves_at=now + timedelta(minutes=TEAM_BATTLE_TIMER_MINUTES),
                now=now,
                payload={
                    "battle_id": battle.id,
                    "challenger_user_id": battle.challenger_user_id,
                    "opponent_user_id": battle.opponent_user_id,
                    "challenger_label": challenger_label,
                    "opponent_label": opponent_label,
                    "side1": [],
                    "side2": [],
                },
            )
            pending = await uow.pending_events.add(pending)
            await uow.commit()
            assert pending.id is not None

            return BattleOpenedResult(
                pending_event_id=pending.id,
                challenger_tg_id=challenger.tg_id,
                opponent_tg_id=opponent.tg_id,
                challenger_label=challenger_label,
                opponent_label=opponent_label,
                stake_cm=battle.stake_cm,
            )


