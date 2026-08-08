from __future__ import annotations

from src.application import dick_history
from src.application.dto.gift import GiftSizeCommand, GiftSizeResult
from src.application.ports.clock import Clock
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.entities.dick import Dick
from src.domain.entities.user import User
from src.domain.exceptions import InsufficientDickSize, SelfInteraction
from src.domain.value_objects.dick_history_reason import DickHistoryReason
from src.domain.value_objects.dick_size import MAX_SIZE_CM
from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId


class GiftSizeUseCase:
    """Transfers dick-size cm from the actor to the target, within a chat."""

    def __init__(self, uow: UnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    async def execute(self, command: GiftSizeCommand) -> GiftSizeResult:
        if command.actor_tg_id == command.target_tg_id:
            raise SelfInteraction()
        if command.amount_cm <= 0:
            raise ValueError("amount must be positive")

        now = self._clock.now()
        async with self._uow as uow:
            actor = await _get_or_create_user(
                uow, command.actor_tg_id, command.actor_username, now
            )
            target = await _get_or_create_user(
                uow, command.target_tg_id, command.target_username, now
            )
            assert actor.id is not None and target.id is not None

            actor_dick = await _get_or_create_dick(uow, actor.id, command.chat_id)
            target_dick = await _get_or_create_dick(uow, target.id, command.chat_id)

            if actor_dick.size.cm < command.amount_cm:
                raise InsufficientDickSize(
                    needed=command.amount_cm, actual=actor_dick.size.cm
                )

            # Cap by the target's remaining headroom too, so a transfer near
            # MAX_SIZE_CM can't take more from the actor than the target can
            # actually receive.
            transfer_cm = min(
                command.amount_cm, MAX_SIZE_CM - target_dick.size.cm
            )
            actor_dick.size = actor_dick.size.apply(-transfer_cm)
            target_dick.size = target_dick.size.apply(transfer_cm)
            await uow.dicks.update(actor_dick)
            await uow.dicks.update(target_dick)
            await dick_history.record(
                uow,
                user_id=actor.id,
                chat_id=command.chat_id,
                delta_cm=-transfer_cm,
                new_size_cm=actor_dick.size.cm,
                reason=DickHistoryReason.GIFT_SENT,
                now=now,
            )
            await dick_history.record(
                uow,
                user_id=target.id,
                chat_id=command.chat_id,
                delta_cm=transfer_cm,
                new_size_cm=target_dick.size.cm,
                reason=DickHistoryReason.GIFT_RECEIVED,
                now=now,
            )
            await uow.commit()

            return GiftSizeResult(
                amount_cm=transfer_cm,
                actor_new_size_cm=actor_dick.size.cm,
                target_new_size_cm=target_dick.size.cm,
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


async def _get_or_create_dick(
    uow: UnitOfWork, user_id: int, chat_id: TelegramChatId
) -> Dick:
    existing = await uow.dicks.get(user_id, chat_id)
    if existing is not None:
        return existing
    return await uow.dicks.add(Dick.initial(user_id, chat_id))
