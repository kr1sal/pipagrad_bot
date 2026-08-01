from __future__ import annotations

from dataclasses import dataclass

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from dishka.integrations.aiogram import FromDishka, inject

from src.application.dto.interaction import (
    InteractionDenied,
    InteractionPerformed,
    PerformInteractionCommand,
)
from src.application.use_cases.find_user_by_username import (
    FindUserByUsernameUseCase,
)
from src.application.use_cases.perform_interaction import PerformInteractionUseCase
from src.domain.exceptions import SelfInteraction
from src.domain.value_objects.interaction_type import InteractionType
from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId
from src.presentation.bot.texts import ru as texts

router = Router(name="interactions")


@dataclass(frozen=True, slots=True)
class _Target:
    tg_id: int
    username: str | None
    display_name: str | None  # only when we know it from a live TG user


async def _resolve_target(
    message: Message,
    command: CommandObject,
    find_user: FindUserByUsernameUseCase,
) -> _Target | None:
    """
    Two ways to name a target:
      1. Reply to their message (most convenient in groups).
      2. `/cmd @username` — looked up in our users table (they must have
         written to the bot at least once for us to know their id).

    Reply takes precedence — if both are given, we go with reply because the
    id there is authoritative.
    """
    replied = message.reply_to_message
    if replied and replied.from_user and not replied.from_user.is_bot:
        u = replied.from_user
        return _Target(tg_id=u.id, username=u.username, display_name=u.full_name)

    if command.args:
        raw = command.args.strip().split()[0]
        username = raw.lstrip("@")
        if username:
            found = await find_user.execute(username)
            if found is not None:
                return _Target(
                    tg_id=int(found.tg_id),
                    username=found.username,
                    display_name=None,
                )
            # tell caller it wasn't reply nor a known username — via sentinel
            return _Target(tg_id=0, username=username, display_name=None)

    return None


async def _handle(
    message: Message,
    command: CommandObject,
    kind: InteractionType,
    use_case: PerformInteractionUseCase,
    find_user: FindUserByUsernameUseCase,
) -> None:
    if message.from_user is None:
        return

    target = await _resolve_target(message, command, find_user)
    if target is None:
        await message.reply(texts.interaction_needs_target(kind))
        return
    if target.tg_id == 0:
        # username was provided but we don't know that user
        assert target.username is not None
        await message.reply(texts.interaction_user_not_found(target.username))
        return

    actor = message.from_user

    try:
        result = await use_case.execute(
            PerformInteractionCommand(
                chat_id=TelegramChatId(message.chat.id),
                actor_tg_id=TelegramUserId(actor.id),
                actor_username=actor.username,
                target_tg_id=TelegramUserId(target.tg_id),
                target_username=target.username,
                kind=kind,
            )
        )
    except SelfInteraction:
        await message.reply(texts.interaction_self())
        return

    if isinstance(result, InteractionDenied):
        await message.reply(
            texts.interaction_denied(
                kind=result.kind,
                reason=result.reason,
                current_ml=result.current_ml,
                cost_ml=result.cost_ml,
            )
        )
        return

    assert isinstance(result, InteractionPerformed)
    await message.reply(
        texts.interaction_done(
            kind=result.kind,
            actor_mention=texts.mention(actor.username, actor.id, actor.full_name),
            target_mention=texts.mention(
                target.username, target.tg_id, target.display_name
            ),
        )
    )


@router.message(Command("pet"))
@inject
async def handle_pet(
    message: Message,
    command: CommandObject,
    perform_interaction: FromDishka[PerformInteractionUseCase],
    find_user: FromDishka[FindUserByUsernameUseCase],
) -> None:
    await _handle(
        message, command, InteractionType.PET, perform_interaction, find_user
    )


@router.message(Command("kiss"))
@inject
async def handle_kiss(
    message: Message,
    command: CommandObject,
    perform_interaction: FromDishka[PerformInteractionUseCase],
    find_user: FromDishka[FindUserByUsernameUseCase],
) -> None:
    await _handle(
        message, command, InteractionType.KISS, perform_interaction, find_user
    )


@router.message(Command("fuck"))
@inject
async def handle_fuck(
    message: Message,
    command: CommandObject,
    perform_interaction: FromDishka[PerformInteractionUseCase],
    find_user: FromDishka[FindUserByUsernameUseCase],
) -> None:
    await _handle(
        message, command, InteractionType.FUCK, perform_interaction, find_user
    )


@router.message(Command("hug"))
@inject
async def handle_hug(
    message: Message,
    command: CommandObject,
    perform_interaction: FromDishka[PerformInteractionUseCase],
    find_user: FromDishka[FindUserByUsernameUseCase],
) -> None:
    await _handle(
        message, command, InteractionType.HUG, perform_interaction, find_user
    )
