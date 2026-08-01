from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.application.ports.clock import Clock
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.entities.pending_event import PendingEventKind
from src.domain.entities.user import User
from src.domain.value_objects.telegram_ids import TelegramUserId


class JoinResult(str, Enum):
    """
    Outcome of joining/toggling a pending event, so the callback handler can
    show the right toast without re-loading state.
    """

    JOINED = "joined"
    LEFT = "left"
    ALREADY_ON_OTHER_SIDE = "already_on_other_side"
    NOT_FOUND = "not_found"


@dataclass(frozen=True, slots=True)
class OrgyJoinCounts:
    joined_count: int


@dataclass(frozen=True, slots=True)
class BotBattleJoinCounts:
    pipa_count: int
    other_count: int
    other_label: str


class JoinOrgyUseCase:
    def __init__(self, uow: UnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    async def execute(
        self,
        event_id: int,
        actor_tg_id: TelegramUserId,
        actor_username: str | None,
    ) -> tuple[JoinResult, OrgyJoinCounts | None]:
        now = self._clock.now()
        async with self._uow as uow:
            pending = await uow.pending_events.get(event_id)
            if pending is None or pending.kind is not PendingEventKind.ORGY:
                return JoinResult.NOT_FOUND, None

            actor = await _get_or_create_user(uow, actor_tg_id, actor_username, now)
            assert actor.id is not None

            participants: list[int] = list(pending.payload.get("participants", []))
            if actor.id in participants:
                participants.remove(actor.id)
                result = JoinResult.LEFT
            else:
                participants.append(actor.id)
                result = JoinResult.JOINED
            pending.payload["participants"] = participants
            await uow.pending_events.update_payload(pending.id, pending.payload)
            await uow.commit()
            return result, OrgyJoinCounts(joined_count=len(participants))


class JoinBotBattleUseCase:
    def __init__(self, uow: UnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    async def execute(
        self,
        event_id: int,
        actor_tg_id: TelegramUserId,
        actor_username: str | None,
        side: str,
    ) -> tuple[JoinResult, BotBattleJoinCounts | None]:
        assert side in ("pipa", "other")
        now = self._clock.now()
        async with self._uow as uow:
            pending = await uow.pending_events.get(event_id)
            if pending is None or pending.kind is not PendingEventKind.BOT_BATTLE:
                return JoinResult.NOT_FOUND, None

            actor = await _get_or_create_user(uow, actor_tg_id, actor_username, now)
            assert actor.id is not None

            pipa: list[int] = list(pending.payload.get("pipa_side", []))
            other: list[int] = list(pending.payload.get("other_side", []))
            other_label: str = pending.payload.get("opponent_bot_label", "бот")

            if actor.id in pipa and side == "other":
                return JoinResult.ALREADY_ON_OTHER_SIDE, None
            if actor.id in other and side == "pipa":
                return JoinResult.ALREADY_ON_OTHER_SIDE, None
            if actor.id in pipa or actor.id in other:
                # already on same side — nothing to change; report as JOINED
                return JoinResult.JOINED, BotBattleJoinCounts(
                    pipa_count=len(pipa), other_count=len(other),
                    other_label=other_label,
                )

            if side == "pipa":
                pipa.append(actor.id)
            else:
                other.append(actor.id)

            pending.payload["pipa_side"] = pipa
            pending.payload["other_side"] = other
            await uow.pending_events.update_payload(pending.id, pending.payload)
            await uow.commit()
            return JoinResult.JOINED, BotBattleJoinCounts(
                pipa_count=len(pipa),
                other_count=len(other),
                other_label=other_label,
            )


async def _get_or_create_user(
    uow: UnitOfWork,
    tg_id: TelegramUserId,
    username: str | None,
    now,
) -> User:
    existing = await uow.users.get_by_tg_id(tg_id)
    if existing is not None:
        return existing
    return await uow.users.add(User.new(tg_id, username, now))
