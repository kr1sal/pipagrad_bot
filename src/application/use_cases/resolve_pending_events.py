from __future__ import annotations

import logging
from dataclasses import dataclass

from src.application.ports.clock import Clock
from src.application.ports.randomizer import Randomizer
from src.application.ports.telegram_gateway import TelegramGateway
from src.application.ports.unit_of_work import UnitOfWork
from src.application.texts import ru as texts
from src.domain.entities.pending_event import (
    BOT_BATTLE_BASE_POT,
    ORGY_BONUS_CM,
    ORGY_COST_ML,
    PendingEvent,
    PendingEventKind,
)
from src.domain.entities.semen_balance import SemenBalance, SemenConfig
from src.domain.services.battle_resolver import resolve as resolve_battle
from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class _Outcome:
    chat_id: TelegramChatId
    message_id: int
    text: str
    # bot-battle-specific: if pipa won, we need to kick this user id after the tx
    kick_user_id: TelegramUserId | None = None


class ResolvePendingEventsUseCase:
    """
    Periodic tick that finalizes every pending event whose resolves_at has
    passed. All DB mutations happen inside a single transaction; message edits
    and kicks are best-effort side effects executed after commit — if any
    external call fails the DB state is already correct.
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
        self._cfg = semen_config

    async def execute(self) -> int:
        now = self._clock.now()
        outcomes: list[_Outcome] = []

        async with self._uow as uow:
            events = await uow.pending_events.list_ready(now)
            for event in events:
                # Commit per event, not once for the whole batch: a bug in
                # resolving one event (e.g. a dangling battle_id) must not
                # roll back — and thereby indefinitely re-block — every other
                # ready event in this tick.
                try:
                    if event.kind is PendingEventKind.ORGY:
                        text = await self._resolve_orgy(event, uow, now)
                        outcome = _Outcome(event.chat_id, event.chat_message_id, text)
                    elif event.kind is PendingEventKind.BOT_BATTLE:
                        text, kick_id = await self._resolve_bot_battle(event, uow)
                        outcome = _Outcome(
                            event.chat_id, event.chat_message_id, text,
                            kick_user_id=kick_id,
                        )
                    elif event.kind is PendingEventKind.TEAM_BATTLE:
                        text = await self._resolve_team_battle(event, uow, now)
                        outcome = _Outcome(event.chat_id, event.chat_message_id, text)
                    else:
                        continue
                    assert event.id is not None
                    await uow.pending_events.delete(event.id)
                    await uow.commit()
                except Exception:  # noqa: BLE001
                    log.exception(
                        "failed to resolve pending event id=%s kind=%s",
                        event.id, event.kind,
                    )
                    await uow.rollback()
                    continue
                outcomes.append(outcome)

        for o in outcomes:
            try:
                await self._telegram.finalize_message(
                    o.chat_id, o.message_id, o.text
                )
            except Exception:  # noqa: BLE001
                log.warning("finalize message failed for chat %s", o.chat_id)
            if o.kick_user_id is not None:
                try:
                    ok = await self._telegram.kick_user(o.chat_id, o.kick_user_id)
                    if not ok:
                        log.info(
                            "bot-battle kick refused (missing perms) chat=%s uid=%s",
                            o.chat_id, o.kick_user_id,
                        )
                except Exception:  # noqa: BLE001
                    log.warning("kick failed for chat %s", o.chat_id)

        return len(outcomes)

    # ---------------------------------------------------------------- orgy

    async def _resolve_orgy(
        self, event: PendingEvent, uow: UnitOfWork, now
    ) -> str:
        participant_ids: list[int] = list(event.payload.get("participants", []))
        succeeded: list[int] = []
        for user_id in participant_ids:
            dick = await uow.dicks.get(user_id, event.chat_id)
            if dick is None:
                continue
            cap = self._cfg.cap_for(dick.size.cm)
            balance = await uow.semen.get(user_id, event.chat_id)
            if balance is None:
                balance = SemenBalance.initial(user_id, event.chat_id, cap, now)
            spent = balance.try_spend(
                ORGY_COST_ML, now, self._cfg.regen_per_hour, cap
            )
            if spent is None:
                continue
            await uow.semen.upsert(balance)
            succeeded.append(user_id)

        if succeeded:
            for user_id in succeeded:
                dick = await uow.dicks.get(user_id, event.chat_id)
                if dick is None:
                    continue
                dick.size = dick.size.apply(ORGY_BONUS_CM)
                await uow.dicks.update(dick)

        if not succeeded:
            return texts.orgy_resolved_nobody(len(participant_ids))
        return texts.orgy_resolved(len(participant_ids), len(succeeded), ORGY_BONUS_CM)

    # ---------------------------------------------------------- bot_battle

    async def _resolve_bot_battle(
        self, event: PendingEvent, uow: UnitOfWork
    ) -> tuple[str, TelegramUserId | None]:
        pipa_ids: list[int] = list(event.payload.get("pipa_side", []))
        other_ids: list[int] = list(event.payload.get("other_side", []))
        other_label: str = event.payload.get("opponent_bot_label", "бот")
        opponent_bot_id: int = int(event.payload.get("opponent_bot_id", 0))

        pipa_pot = BOT_BATTLE_BASE_POT + await _sum_sizes(uow, event.chat_id, pipa_ids)
        other_pot = BOT_BATTLE_BASE_POT + await _sum_sizes(uow, event.chat_id, other_ids)
        total = pipa_pot + other_pot
        roll = self._rng.int_between(1, total) if total > 0 else 1
        pipa_wins = roll <= pipa_pot

        if pipa_wins:
            text = texts.bot_battle_resolved_pipa_won(other_label, pipa_pot, other_pot)
            return text, TelegramUserId(opponent_bot_id) if opponent_bot_id else None

        text = texts.bot_battle_resolved_other_won(other_label, pipa_pot, other_pot)
        return text, None

    # --------------------------------------------------------- team battle

    async def _resolve_team_battle(
        self, event: PendingEvent, uow: UnitOfWork, now
    ) -> str:
        battle_id = int(event.payload["battle_id"])
        battle = await uow.battles.get(battle_id)
        assert battle is not None

        side1: list[int] = list(event.payload.get("side1", []))
        side2: list[int] = list(event.payload.get("side2", []))
        challenger_label: str = event.payload.get("challenger_label", "?")
        opponent_label: str = event.payload.get("opponent_label", "?")

        # Chance depends only on headcount per side, not dick size.
        side1_count = 1 + len(side1)
        side2_count = 1 + len(side2)
        roll = self._rng.int_between(1, side1_count + side2_count)
        side1_wins = resolve_battle(side1_count, side2_count, roll).challenger_wins

        challenger_dick = await uow.dicks.get(battle.challenger_user_id, battle.chat_id)
        opponent_dick = await uow.dicks.get(battle.opponent_user_id, battle.chat_id)
        assert challenger_dick is not None and opponent_dick is not None

        if side1_wins:
            winner_dick, loser_dick = challenger_dick, opponent_dick
            winner_user_id = battle.challenger_user_id
            winner_label, loser_label = challenger_label, opponent_label
            winner_count, loser_count = side1_count, side2_count
        else:
            winner_dick, loser_dick = opponent_dick, challenger_dick
            winner_user_id = battle.opponent_user_id
            winner_label, loser_label = opponent_label, challenger_label
            winner_count, loser_count = side2_count, side1_count

        # Re-derive the actual transfer instead of trusting battle.stake_cm:
        # the loser's size may have dropped below the staked amount since
        # accept-time (e.g. via /gift or another battle during the join
        # window), and DickSize.apply() clamps at 0 — independently applying
        # +stake to the winner and -stake to the loser would then mint cm
        # out of nowhere instead of transferring what the loser actually has.
        transfer_cm = min(battle.stake_cm, loser_dick.size.cm)
        winner_dick.size = winner_dick.size.apply(transfer_cm)
        loser_dick.size = loser_dick.size.apply(-transfer_cm)
        await uow.dicks.update(winner_dick)
        await uow.dicks.update(loser_dick)

        battle.resolve(winner_user_id=winner_user_id, now=now)
        await uow.battles.update(battle)

        return texts.team_battle_resolved(
            winner_label, loser_label, transfer_cm,
            winner_dick.size.cm, loser_dick.size.cm,
            winner_count, loser_count,
        )


async def _sum_sizes(
    uow: UnitOfWork, chat_id: TelegramChatId, user_ids: list[int]
) -> int:
    total = 0
    for uid in user_ids:
        dick = await uow.dicks.get(uid, chat_id)
        if dick is not None:
            total += dick.size.cm
    return total
