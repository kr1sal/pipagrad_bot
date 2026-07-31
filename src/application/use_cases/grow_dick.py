from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from src.application.dto.grow_dick import (
    GrowDickCommand,
    GrowDickCooldown,
    GrowDickResult,
)
from src.application.ports.clock import Clock
from src.application.ports.randomizer import Randomizer
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.entities.dick import Dick
from src.domain.entities.user import User
from src.domain.exceptions import CooldownActive


@dataclass(frozen=True, slots=True)
class GrowDickConfig:
    cooldown: timedelta
    min_delta_cm: int
    max_delta_cm: int


class GrowDickUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        randomizer: Randomizer,
        config: GrowDickConfig,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._randomizer = randomizer
        self._config = config

    async def execute(
        self, command: GrowDickCommand
    ) -> GrowDickResult | GrowDickCooldown:
        now = self._clock.now()
        async with self._uow as uow:
            user = await uow.users.get_by_tg_id(command.tg_user_id)
            if user is None:
                user = await uow.users.add(
                    User.new(command.tg_user_id, command.tg_username, now)
                )
            assert user.id is not None

            dick = await uow.dicks.get(user.id, command.chat_id)
            if dick is None:
                dick = await uow.dicks.add(Dick.initial(user.id, command.chat_id))
            assert dick.id is not None

            try:
                delta_cm = self._randomizer.int_between(
                    self._config.min_delta_cm, self._config.max_delta_cm
                )
                applied = dick.grow(delta_cm, now, self._config.cooldown)
            except CooldownActive as e:
                return GrowDickCooldown(
                    remaining=e.remaining, current_size_cm=dick.size.cm
                )

            await uow.dicks.update(dick)
            await uow.commit()
            return GrowDickResult(delta_cm=applied, new_size_cm=dick.size.cm)
