from __future__ import annotations

import logging
from dataclasses import dataclass

from src.application.ports.clock import Clock
from src.application.ports.randomizer import Randomizer
from src.application.ports.telegram_gateway import TelegramGateway
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.entities.dick import Dick
from src.domain.entities.group import Group
from src.domain.services.battle_resolver import resolve as resolve_battle
from src.domain.value_objects.random_event_kind import RandomEventKind
from src.domain.value_objects.telegram_ids import TelegramChatId

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class _Notification:
    chat_id: TelegramChatId
    text: str


ALL_KINDS: tuple[RandomEventKind, ...] = (
    RandomEventKind.METEOR,
    RandomEventKind.RADIATION,
    RandomEventKind.SPONTANEOUS_BATTLE,
)


class TriggerRandomEventsCycleUseCase:
    """
    Periodic tick: pick every group whose interval has elapsed, roll one event,
    apply mutations transactionally, then fan out chat notifications after commit.
    Notifications are best-effort — a failed send doesn't roll back the effect.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        randomizer: Randomizer,
        telegram: TelegramGateway,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._rng = randomizer
        self._telegram = telegram

    async def execute(self) -> int:
        """Returns the number of events fired this cycle."""
        now = self._clock.now()
        notifications: list[_Notification] = []

        async with self._uow as uow:
            groups = await uow.groups.list_with_random_events_ready(now)
            for group in groups:
                dicks = await uow.dicks.list_for_chat(group.chat_id)
                if not dicks:
                    continue

                kind = self._rng.choice(ALL_KINDS)
                text = await self._apply(kind, group, dicks, uow)
                if text is None:
                    # event could not be applied (e.g. spontaneous battle
                    # without two eligible players); skip without marking so
                    # the next tick re-tries a different event
                    continue

                await uow.groups.mark_random_event_fired(group.chat_id, now)
                notifications.append(_Notification(group.chat_id, text))
            await uow.commit()

        for n in notifications:
            try:
                await self._telegram.send_message(n.chat_id, n.text)
            except Exception:  # noqa: BLE001
                log.warning("random-event notify failed for chat %s", n.chat_id)

        return len(notifications)

    async def _apply(
        self,
        kind: RandomEventKind,
        group: Group,
        dicks: list[Dick],
        uow: UnitOfWork,
    ) -> str | None:
        if kind is RandomEventKind.METEOR:
            return await self._meteor(dicks, uow)
        if kind is RandomEventKind.RADIATION:
            return await self._radiation(dicks, uow)
        if kind is RandomEventKind.SPONTANEOUS_BATTLE:
            return await self._spontaneous_battle(dicks, uow)
        return None

    async def _meteor(self, dicks: list[Dick], uow: UnitOfWork) -> str:
        target = self._rng.choice(dicks)
        loss = self._rng.int_between(3, 10)
        target.size = target.size.apply(-loss)
        await uow.dicks.update(target)
        return (
            f"☄️ <b>Метеорит</b> упал в чат и попал по одному из вас!\n"
            f"−{loss} см — новый размер: <b>{target.size.cm} см</b>"
        )

    async def _radiation(self, dicks: list[Dick], uow: UnitOfWork) -> str:
        gained = lost = 0
        for d in dicks:
            delta = self._rng.int_between(-2, 5)
            new = d.size.apply(delta)
            applied = new.cm - d.size.cm
            d.size = new
            await uow.dicks.update(d)
            if applied > 0:
                gained += 1
            elif applied < 0:
                lost += 1
        return (
            f"☢️ <b>Радиация</b> прошла по чату. "
            f"Выросли: {gained}, уменьшились: {lost}."
        )

    async def _spontaneous_battle(
        self, dicks: list[Dick], uow: UnitOfWork
    ) -> str | None:
        stake = 5
        eligible = [d for d in dicks if d.size.cm >= stake]
        if len(eligible) < 2:
            return None
        a, b = self._rng.sample(eligible, 2)
        total = a.size.cm + b.size.cm
        roll = self._rng.int_between(1, total) if total > 0 else 0
        outcome = resolve_battle(a.size.cm, b.size.cm, roll)
        winner, loser = (a, b) if outcome.challenger_wins else (b, a)

        winner.size = winner.size.apply(stake)
        loser.size = loser.size.apply(-stake)
        await uow.dicks.update(winner)
        await uow.dicks.update(loser)

        winner_user = await uow.users.get_by_id(winner.user_id)
        loser_user = await uow.users.get_by_id(loser.user_id)
        assert winner_user is not None and loser_user is not None
        winner_ref = _user_ref(winner_user.username, int(winner_user.tg_id))
        loser_ref = _user_ref(loser_user.username, int(loser_user.tg_id))
        return (
            f"⚔️ <b>Внезапная битва!</b>\n"
            f"{winner_ref} побеждает {loser_ref} и забирает {stake} см.\n"
            f"Победитель: <b>{winner.size.cm} см</b> / "
            f"Проигравший: <b>{loser.size.cm} см</b>"
        )


def _user_ref(username: str | None, tg_id: int) -> str:
    from html import escape

    label = f"@{username}" if username else f"id{tg_id}"
    return f'<a href="tg://user?id={tg_id}">{escape(label)}</a>'


