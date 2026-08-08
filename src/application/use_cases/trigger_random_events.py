from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from src.application import dick_history
from src.application.ports.clock import Clock
from src.application.ports.randomizer import Randomizer
from src.application.ports.telegram_gateway import BotAdmin, TelegramGateway
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.entities.dick import Dick
from src.domain.entities.group import Group
from src.domain.entities.pending_event import (
    BOT_BATTLE_TIMER_MINUTES,
    ORGY_TIMER_MINUTES,
    PendingEvent,
    PendingEventKind,
)
from src.domain.entities.semen_balance import SemenBalance, SemenConfig
from src.domain.services.battle_resolver import resolve as resolve_battle
from src.domain.value_objects.dick_history_reason import DickHistoryReason
from src.domain.value_objects.random_event_kind import RandomEventKind
from src.domain.value_objects.telegram_ids import TelegramChatId
from src.application.texts import ru as texts

log = logging.getLogger(__name__)

INTERVAL_MIN_HOURS = 12
INTERVAL_MAX_HOURS = 24

# Roughly-tuned weights so pending events (orgy, bot_battle) stay rare — the
# bot battle in particular can only fire when another bot admin is around.
_WEIGHTS: dict[RandomEventKind, int] = {
    RandomEventKind.METEOR: 15,
    RandomEventKind.RADIATION: 15,
    RandomEventKind.SPONTANEOUS_BATTLE: 15,
    RandomEventKind.HURRICANE: 15,
    RandomEventKind.GIFT: 15,
    RandomEventKind.VIAGRA: 10,
    RandomEventKind.ICE_AGE: 10,
    RandomEventKind.ROYAL_BATTLE: 5,
    RandomEventKind.ORGY: 5,
    RandomEventKind.BOT_BATTLE: 1,
}
_WEIGHTED_KINDS: list[RandomEventKind] = [
    k for k, w in _WEIGHTS.items() for _ in range(w)
]
_MAX_PICK_ATTEMPTS = 4


@dataclass(frozen=True, slots=True)
class _Notification:
    chat_id: TelegramChatId
    text: str


@dataclass(frozen=True, slots=True)
class _EventOutcome:
    fired: bool  # True → advance the timer
    notify_text: str | None  # if set, post to chat after commit


_SKIPPED = _EventOutcome(fired=False, notify_text=None)
_HANDLED_INLINE = _EventOutcome(fired=True, notify_text=None)


def _spoken(text: str) -> _EventOutcome:
    return _EventOutcome(fired=True, notify_text=text)


class TriggerRandomEventsCycleUseCase:
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
        fired_count = 0

        async with self._uow as uow:
            groups = await uow.groups.list_with_random_events_ready(now)
            for group in groups:
                dicks = await uow.dicks.list_for_chat(group.chat_id)
                if not dicks:
                    continue

                outcome = await self._roll_and_apply(group, dicks, uow, now)
                if not outcome.fired:
                    continue

                next_at = now + timedelta(
                    hours=self._rng.int_between(INTERVAL_MIN_HOURS, INTERVAL_MAX_HOURS)
                )
                await uow.groups.mark_random_event_fired(group.chat_id, next_at)
                fired_count += 1
                if outcome.notify_text:
                    notifications.append(
                        _Notification(group.chat_id, outcome.notify_text)
                    )
            await uow.commit()

        for n in notifications:
            try:
                await self._telegram.send_message(n.chat_id, n.text)
            except Exception:  # noqa: BLE001
                log.warning("random-event notify failed for chat %s", n.chat_id)

        return fired_count

    async def _roll_and_apply(
        self, group: Group, dicks: list[Dick], uow: UnitOfWork, now: datetime
    ) -> _EventOutcome:
        for _ in range(_MAX_PICK_ATTEMPTS):
            kind = self._rng.choice(_WEIGHTED_KINDS)
            if kind is RandomEventKind.METEOR:
                return _spoken(await self._meteor(dicks, uow, now))
            if kind is RandomEventKind.RADIATION:
                return _spoken(await self._radiation(dicks, uow, now))
            if kind is RandomEventKind.SPONTANEOUS_BATTLE:
                text = await self._spontaneous_battle(dicks, uow, now)
                if text is None:
                    continue
                return _spoken(text)
            if kind is RandomEventKind.HURRICANE:
                return _spoken(await self._hurricane(dicks, uow, now))
            if kind is RandomEventKind.GIFT:
                return _spoken(await self._gift(dicks, uow, now))
            if kind is RandomEventKind.VIAGRA:
                return _spoken(await self._viagra(dicks, uow, now))
            if kind is RandomEventKind.ICE_AGE:
                return _spoken(await self._ice_age(dicks, uow))
            if kind is RandomEventKind.ROYAL_BATTLE:
                text = await self._royal_battle(dicks, uow, now)
                if text is None:
                    continue
                return _spoken(text)
            if kind is RandomEventKind.ORGY:
                ok = await self._create_orgy(group.chat_id, uow, now)
                if not ok:
                    continue
                return _HANDLED_INLINE
            if kind is RandomEventKind.BOT_BATTLE:
                ok = await self._create_bot_battle(group.chat_id, uow, now)
                if not ok:
                    continue
                return _HANDLED_INLINE
        return _SKIPPED

    # ------------------------------------------------------------ immediate

    async def _meteor(self, dicks: list[Dick], uow: UnitOfWork, now: datetime) -> str:
        target = self._rng.choice(dicks)
        loss = self._rng.int_between(3, 10)
        old_cm = target.size.cm
        target.size = target.size.apply(-loss)
        await uow.dicks.update(target)
        await dick_history.record(
            uow,
            user_id=target.user_id,
            chat_id=target.chat_id,
            delta_cm=target.size.cm - old_cm,
            new_size_cm=target.size.cm,
            reason=DickHistoryReason.METEOR,
            now=now,
        )
        return texts.meteor(loss, target.size.cm)

    async def _radiation(self, dicks: list[Dick], uow: UnitOfWork, now: datetime) -> str:
        gained = lost = 0
        for d in dicks:
            delta = self._rng.int_between(-2, 5)
            new = d.size.apply(delta)
            applied = new.cm - d.size.cm
            d.size = new
            await uow.dicks.update(d)
            await dick_history.record(
                uow,
                user_id=d.user_id,
                chat_id=d.chat_id,
                delta_cm=applied,
                new_size_cm=d.size.cm,
                reason=DickHistoryReason.RADIATION,
                now=now,
            )
            if applied > 0:
                gained += 1
            elif applied < 0:
                lost += 1
        return texts.radiation(gained, lost)

    async def _spontaneous_battle(
        self, dicks: list[Dick], uow: UnitOfWork, now: datetime
    ) -> str | None:
        stake = 5
        eligible = [d for d in dicks if d.size.cm >= stake]
        if len(eligible) < 2:
            return None
        a, b = self._rng.sample(eligible, 2)
        total = a.size.cm + b.size.cm
        roll = (
            self._rng.int_between(1, total)
            if total > 0
            else self._rng.int_between(0, 1)
        )
        outcome = resolve_battle(a.size.cm, b.size.cm, roll)
        winner, loser = (a, b) if outcome.challenger_wins else (b, a)

        winner.size = winner.size.apply(stake)
        loser.size = loser.size.apply(-stake)
        await uow.dicks.update(winner)
        await uow.dicks.update(loser)
        await dick_history.record(
            uow,
            user_id=winner.user_id,
            chat_id=winner.chat_id,
            delta_cm=stake,
            new_size_cm=winner.size.cm,
            reason=DickHistoryReason.SPONTANEOUS_BATTLE,
            now=now,
        )
        await dick_history.record(
            uow,
            user_id=loser.user_id,
            chat_id=loser.chat_id,
            delta_cm=-stake,
            new_size_cm=loser.size.cm,
            reason=DickHistoryReason.SPONTANEOUS_BATTLE,
            now=now,
        )

        winner_ref = await _label_by_user_id(uow, winner.user_id)
        loser_ref = await _label_by_user_id(uow, loser.user_id)
        return texts.spontaneous_battle(
            winner_ref, loser_ref, stake, winner.size.cm, loser.size.cm
        )

    async def _hurricane(self, dicks: list[Dick], uow: UnitOfWork, now: datetime) -> str:
        n_hit = max(1, len(dicks) // 2)
        victims = self._rng.sample(dicks, min(n_hit, len(dicks)))
        total_loss = 0
        for d in victims:
            loss = self._rng.int_between(1, 3)
            old_cm = d.size.cm
            d.size = d.size.apply(-loss)
            total_loss += loss
            await uow.dicks.update(d)
            await dick_history.record(
                uow,
                user_id=d.user_id,
                chat_id=d.chat_id,
                delta_cm=d.size.cm - old_cm,
                new_size_cm=d.size.cm,
                reason=DickHistoryReason.HURRICANE,
                now=now,
            )
        return texts.hurricane(len(victims), total_loss)

    async def _gift(self, dicks: list[Dick], uow: UnitOfWork, now: datetime) -> str:
        target = self._rng.choice(dicks)
        bonus = self._rng.int_between(5, 15)
        old_cm = target.size.cm
        target.size = target.size.apply(bonus)
        await uow.dicks.update(target)
        await dick_history.record(
            uow,
            user_id=target.user_id,
            chat_id=target.chat_id,
            delta_cm=target.size.cm - old_cm,
            new_size_cm=target.size.cm,
            reason=DickHistoryReason.RANDOM_GIFT,
            now=now,
        )
        ref = await _label_by_user_id(uow, target.user_id)
        return texts.gift(ref, bonus, target.size.cm)

    async def _viagra(self, dicks: list[Dick], uow: UnitOfWork, now: datetime) -> str:
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
        return texts.viagra(len(dicks))

    async def _ice_age(self, dicks: list[Dick], uow: UnitOfWork) -> str:
        reset = 0
        for d in dicks:
            if d.last_grow_at is not None:
                d.last_grow_at = None
                await uow.dicks.update(d)
                reset += 1
        if reset == 0:
            return texts.ice_age_no_effect()
        return texts.ice_age(reset)

    async def _royal_battle(
        self, dicks: list[Dick], uow: UnitOfWork, now: datetime
    ) -> str | None:
        eligible = [d for d in dicks if d.size.cm >= 5]
        if len(eligible) < 4:
            return None
        players = self._rng.sample(eligible, 4)
        a, b, c, d = players

        semi1_winner, semi1_loser = self._duel(a, b)
        semi2_winner, semi2_loser = self._duel(c, d)
        champion, finalist = self._duel(semi1_winner, semi2_winner)

        nominal_deltas = {
            id(champion): 9, id(finalist): 3, id(semi1_loser): -3, id(semi2_loser): -3,
        }
        for p in (champion, finalist, semi1_loser, semi2_loser):
            old_cm = p.size.cm
            p.size = p.size.apply(nominal_deltas[id(p)])
            await uow.dicks.update(p)
            await dick_history.record(
                uow,
                user_id=p.user_id,
                chat_id=p.chat_id,
                delta_cm=p.size.cm - old_cm,
                new_size_cm=p.size.cm,
                reason=DickHistoryReason.ROYAL_BATTLE,
                now=now,
            )

        champ_ref = await _label_by_user_id(uow, champion.user_id)
        fin_ref = await _label_by_user_id(uow, finalist.user_id)
        return texts.royal_battle(
            champ_ref, champion.size.cm, fin_ref, finalist.size.cm
        )

    def _duel(self, a: Dick, b: Dick) -> tuple[Dick, Dick]:
        total = a.size.cm + b.size.cm
        roll = (
            self._rng.int_between(1, total)
            if total > 0
            else self._rng.int_between(0, 1)
        )
        outcome = resolve_battle(a.size.cm, b.size.cm, roll)
        return (a, b) if outcome.challenger_wins else (b, a)

    # -------------------------------------------------------------- pending

    async def _create_orgy(
        self, chat_id: TelegramChatId, uow: UnitOfWork, now: datetime
    ) -> bool:
        resolves_at = now + timedelta(minutes=ORGY_TIMER_MINUTES)
        pending = PendingEvent.new(
            chat_id=chat_id,
            kind=PendingEventKind.ORGY,
            chat_message_id=0,
            resolves_at=resolves_at,
            now=now,
            payload={"participants": []},
        )
        pending = await uow.pending_events.add(pending)
        assert pending.id is not None

        text = texts.orgy_announcement(ORGY_TIMER_MINUTES)
        try:
            message_id = await self._telegram.announce_orgy(
                chat_id, text, pending.id
            )
        except Exception:  # noqa: BLE001
            log.warning("orgy announcement failed for chat %s", chat_id)
            return False
        await uow.pending_events.set_message_id(pending.id, message_id)
        return True

    async def _create_bot_battle(
        self, chat_id: TelegramChatId, uow: UnitOfWork, now: datetime
    ) -> bool:
        bots = await self._telegram.list_bot_admins(chat_id)
        if not bots:
            return False
        opponent: BotAdmin = self._rng.choice(bots)
        resolves_at = now + timedelta(minutes=BOT_BATTLE_TIMER_MINUTES)
        label = opponent.username or opponent.full_name

        payload = {
            "opponent_bot_id": int(opponent.tg_id),
            "opponent_bot_label": label,
            "pipa_side": [],
            "other_side": [],
        }
        pending = PendingEvent.new(
            chat_id=chat_id,
            kind=PendingEventKind.BOT_BATTLE,
            chat_message_id=0,
            resolves_at=resolves_at,
            now=now,
            payload=payload,
        )
        pending = await uow.pending_events.add(pending)
        assert pending.id is not None

        text = texts.bot_battle_announcement(BOT_BATTLE_TIMER_MINUTES, label)
        try:
            message_id = await self._telegram.announce_bot_battle(
                chat_id, text, pending.id, label
            )
        except Exception:  # noqa: BLE001
            log.warning("bot-battle announcement failed for chat %s", chat_id)
            return False
        await uow.pending_events.set_message_id(pending.id, message_id)
        return True


async def _label_by_user_id(uow: UnitOfWork, user_id: int) -> str:
    from html import escape

    user = await uow.users.get_by_id(user_id)
    if user is None:
        return f"id{user_id}"
    tg_id = int(user.tg_id)
    label = user.username or f"id{tg_id}"
    return escape(label)
