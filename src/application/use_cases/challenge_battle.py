from __future__ import annotations

from src.application.dto.battle import BattleChallenged, ChallengeBattleCommand
from src.application.ports.clock import Clock
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.entities.battle import Battle
from src.domain.entities.dick import Dick
from src.domain.entities.group import Group
from src.domain.entities.user import User
from src.domain.exceptions import (
    BattleAlreadyActive,
    BattlesDisabled,
    InsufficientDickSize,
    SelfInteraction,
)
from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId


class ChallengeBattleUseCase:
    def __init__(self, uow: UnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    async def execute(self, command: ChallengeBattleCommand) -> BattleChallenged:
        if command.challenger_tg_id == command.opponent_tg_id:
            raise SelfInteraction()
        if command.stake_cm <= 0:
            raise ValueError("stake must be positive")

        now = self._clock.now()
        async with self._uow as uow:
            group = await _get_or_create_group(uow, command.chat_id, now)
            if not group.settings.battles_enabled:
                raise BattlesDisabled()

            challenger = await _get_or_create_user(
                uow, command.challenger_tg_id, command.challenger_username, now
            )
            opponent = await _get_or_create_user(
                uow, command.opponent_tg_id, command.opponent_username, now
            )
            assert challenger.id is not None and opponent.id is not None

            active = await uow.battles.get_active_between(
                command.chat_id, challenger.id, opponent.id
            )
            if active is not None:
                raise BattleAlreadyActive()

            challenger_dick = await _get_or_create_dick(
                uow, challenger.id, command.chat_id
            )
            opponent_dick = await _get_or_create_dick(
                uow, opponent.id, command.chat_id
            )

            if challenger_dick.size.cm < command.stake_cm:
                raise InsufficientDickSize(
                    needed=command.stake_cm, actual=challenger_dick.size.cm
                )
            if opponent_dick.size.cm < command.stake_cm:
                raise InsufficientDickSize(
                    needed=command.stake_cm, actual=opponent_dick.size.cm
                )

            battle = Battle.new(
                chat_id=command.chat_id,
                challenger_user_id=challenger.id,
                opponent_user_id=opponent.id,
                stake_cm=command.stake_cm,
                now=now,
            )
            saved = await uow.battles.add(battle)
            await uow.commit()
            assert saved.id is not None
            return BattleChallenged(battle_id=saved.id, stake_cm=command.stake_cm)


async def _get_or_create_group(
    uow: UnitOfWork, chat_id: TelegramChatId, now
) -> Group:
    existing = await uow.groups.get(chat_id)
    if existing is not None:
        return existing
    return await uow.groups.add(
        Group.new(chat_id=chat_id, title=None, added_by_tg_id=None, now=now)
    )


async def _get_or_create_user(
    uow: UnitOfWork, tg_id: TelegramUserId, username: str | None, now
) -> User:
    existing = await uow.users.get_by_tg_id(tg_id)
    if existing is not None:
        return existing
    return await uow.users.add(User.new(tg_id, username, now))


async def _get_or_create_dick(
    uow: UnitOfWork, user_id: int, chat_id: TelegramChatId
) -> Dick:
    existing = await uow.dicks.get(user_id, chat_id)
    if existing is not None:
        return existing
    return await uow.dicks.add(Dick.initial(user_id, chat_id))
