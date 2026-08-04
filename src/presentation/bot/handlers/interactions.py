from __future__ import annotations

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
from src.domain.value_objects.telegram_ids import TelegramUserId
from src.presentation.bot.handlers.scope import resolve_scope_chat_id
from src.presentation.bot.handlers.target_resolution import resolve_target
from src.presentation.bot.texts import ru as texts

router = Router(name="interactions")


async def _handle(
    message: Message,
    command: CommandObject,
    kind: InteractionType,
    use_case: PerformInteractionUseCase,
    find_user: FindUserByUsernameUseCase,
) -> None:
    if message.from_user is None:
        return

    raw_username = command.args.strip().split()[0] if command.args else None
    target = await resolve_target(message, raw_username, find_user)
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
                chat_id=resolve_scope_chat_id(message.chat),
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
