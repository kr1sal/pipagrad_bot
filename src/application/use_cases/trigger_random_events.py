from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta

from src.application.ports.clock import Clock
from src.application.ports.randomizer import Randomizer
from src.application.ports.telegram_gateway import TelegramGateway
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.entities.dick import Dick
from src.domain.entities.group import Group
from src.domain.entities.semen_balance import SemenBalance, SemenConfig
from src.domain.services.battle_resolver import resolve as resolve_battle
from src.domain.value_objects.random_event_kind import RandomEventKind
from src.domain.value_objects.telegram_ids import TelegramChatId

log = logging.getLogger(__name__)

# Interval between random events per chat is chosen uniformly from this range,
# re-rolled after each fire. Hardcoded so admins can't grind the mechanic; the
# only knob remaining in /settings is the on/off toggle.
INTERVAL_MIN_HOURS = 12
INTERVAL_MAX_HOURS = 24


@dataclass(frozen=True, slots=True)
class _Notification:
    chat_id: TelegramChatId
    text: str


ALL_KINDS: tuple[RandomEventKind, ...] = (
    RandomEventKind.METEOR,
    RandomEventKind.RADIATION,
    RandomEventKind.SPONTANEOUS_BATTLE,
    RandomEventKind.HURRICANE,
    RandomEventKind.GIFT,
    RandomEventKind.VIAGRA,
    RandomEventKind.ICE_AGE,
    RandomEventKind.ROYAL_BATTLE,
)


class TriggerRandomEventsCycleUseCase:
    """
    Periodic tick: for every group that's due, roll one event, apply mutations
    transactionally, then fan out chat notifications after commit. Best-effort
    delivery — a failed send doesn't roll back the effect.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        clock: Clock,
        randomizer: Randomizer,
        telegram: TelegramGateway,
        semen_config: SemenConfig,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._rng = randomizer
        self._telegram = telegram
        self._semen_config = semen_config

    async def execute(self) -> int:
        now = self._clock.now()
        notifications: list[_Notification] = []

        async with self._uow as uow:
            groups = await uow.groups.list_with_random_events_ready(now)
            for group in groups:
                dicks = await uow.dicks.list_for_chat(group.chat_id)
                if not dicks:
                    continue

                kind = self._rng.choice(ALL_KINDS)
                text = await self._apply(kind, group, dicks, uow, now)
                if text is None:
                    # event bailed (not enough eligible players etc.); don't
                    # advance the timer so the next tick can try again soon
                    continue

                next_at = now + timedelta(
                    hours=self._rng.int_between(INTERVAL_MIN_HOURS, INTERVAL_MAX_HOURS)
                )
                await uow.groups.mark_random_event_fired(group.chat_id, next_at)
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
        now,
    ) -> str | None:
        if kind is RandomEventKind.METEOR:
            return await self._meteor(dicks, uow)
        if kind is RandomEventKind.RADIATION:
            return await self._radiation(dicks, uow)
        if kind is RandomEventKind.SPONTANEOUS_BATTLE:
            return await self._spontaneous_battle(dicks, uow)
        if kind is RandomEventKind.HURRICANE:
            return await self._hurricane(dicks, uow)
        if kind is RandomEventKind.GIFT:
            return await self._gift(dicks, uow)
        if kind is RandomEventKind.VIAGRA:
            return await self._viagra(dicks, uow, now)
        if kind is RandomEventKind.ICE_AGE:
            return await self._ice_age(dicks, uow)
        if kind is RandomEventKind.ROYAL_BATTLE:
            return await self._royal_battle(dicks, uow)
        return None

    # ------------------------------------------------------------ existing 3

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

        winner_ref = await _mention_by_user_id(uow, winner.user_id)
        loser_ref = await _mention_by_user_id(uow, loser.user_id)
        return (
            f"⚔️ <b>Внезапная битва!</b>\n"
            f"{winner_ref} побеждает {loser_ref} и забирает {stake} см.\n"
            f"Победитель: <b>{winner.size.cm} см</b> / "
            f"Проигравший: <b>{loser.size.cm} см</b>"
        )

    # ---------------------------------------------------------------- new 5

    async def _hurricane(self, dicks: list[Dick], uow: UnitOfWork) -> str:
        """Half the players lose 1-3 cm each."""
        n_hit = max(1, len(dicks) // 2)
        victims = self._rng.sample(dicks, min(n_hit, len(dicks)))
        total_loss = 0
        for d in victims:
            loss = self._rng.int_between(1, 3)
            d.size = d.size.apply(-loss)
            total_loss += loss
            await uow.dicks.update(d)
        return (
            f"🌪 <b>Ураган</b> сметает половину чата!\n"
            f"Пострадало: {len(victims)} игрок(-ов), суммарно −{total_loss} см."
        )

    async def _gift(self, dicks: list[Dick], uow: UnitOfWork) -> str:
        target = self._rng.choice(dicks)
        bonus = self._rng.int_between(5, 15)
        target.size = target.size.apply(bonus)
        await uow.dicks.update(target)
        ref = await _mention_by_user_id(uow, target.user_id)
        return (
            f"🎁 <b>Подарок с небес!</b>\n"
            f"{ref} получает <b>+{bonus} см</b>. Новый размер: "
            f"<b>{target.size.cm} см</b>."
        )

    async def _viagra(
        self, dicks: list[Dick], uow: UnitOfWork, now
    ) -> str:
        """Refill everyone's semen to their current cap."""
        cfg = self._semen_config
        for d in dicks:
            cap = cfg.cap_for(d.size.cm)
            balance = await uow.semen.get(d.user_id, d.chat_id)
            if balance is None:
                balance = SemenBalance.initial(d.user_id, d.chat_id, cap, now)
            else:
                balance.stored_ml = cap
                balance.updated_at = now
            await uow.semen.upsert(balance)
        return (
            f"💊 <b>Виагра!</b>\n"
            f"У всех {len(dicks)} игрок(-ов) сперма мгновенно до максимума."
        )

    async def _ice_age(self, dicks: list[Dick], uow: UnitOfWork) -> str:
        """Reset /grow cooldown for everyone."""
        reset = 0
        for d in dicks:
            if d.last_grow_at is not None:
                d.last_grow_at = None
                await uow.dicks.update(d)
                reset += 1
        if reset == 0:
            return "🥶 <b>Заморозка</b> прошла впустую — никто не был на кулдауне."
        return (
            f"🥶 <b>Ледниковый период!</b>\n"
            f"Cooldown /grow сброшен у <b>{reset}</b> игрок(-ов) — можно снова расти."
        )

    async def _royal_battle(
        self, dicks: list[Dick], uow: UnitOfWork
    ) -> str | None:
        """4-player tournament: two semis, then a final."""
        eligible = [d for d in dicks if d.size.cm >= 5]
        if len(eligible) < 4:
            return None
        players = self._rng.sample(eligible, 4)
        a, b, c, d = players

        semi1_winner, semi1_loser = self._duel(a, b)
        semi2_winner, semi2_loser = self._duel(c, d)
        champion, finalist = self._duel(semi1_winner, semi2_winner)

        # rewards: champion +9, finalist +3, semi-losers -3
        champion.size = champion.size.apply(9)
        finalist.size = finalist.size.apply(3)
        semi1_loser.size = semi1_loser.size.apply(-3)
        semi2_loser.size = semi2_loser.size.apply(-3)
        for p in (champion, finalist, semi1_loser, semi2_loser):
            await uow.dicks.update(p)

        champ_ref = await _mention_by_user_id(uow, champion.user_id)
        fin_ref = await _mention_by_user_id(uow, finalist.user_id)
        return (
            f"👑 <b>Королевская битва!</b>\n"
            f"🥇 {champ_ref} — <b>+9 см</b>, теперь <b>{champion.size.cm} см</b>\n"
            f"🥈 {fin_ref} — <b>+3 см</b>, теперь <b>{finalist.size.cm} см</b>\n"
            f"Полуфиналисты выбывают с −3 см."
        )

    def _duel(self, a: Dick, b: Dick) -> tuple[Dick, Dick]:
        total = a.size.cm + b.size.cm
        roll = self._rng.int_between(1, total) if total > 0 else 0
        outcome = resolve_battle(a.size.cm, b.size.cm, roll)
        return (a, b) if outcome.challenger_wins else (b, a)


async def _mention_by_user_id(uow: UnitOfWork, user_id: int) -> str:
    """Format an HTML mention for a user we only have by internal id."""
    from html import escape

    user = await uow.users.get_by_id(user_id)
    if user is None:
        return f"id{user_id}"
    tg_id = int(user.tg_id)
    label = f"@{user.username}" if user.username else f"id{tg_id}"
    return f'<a href="tg://user?id={tg_id}">{escape(label)}</a>'
