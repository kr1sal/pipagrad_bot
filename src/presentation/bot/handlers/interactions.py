from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from dishka.integrations.aiogram import FromDishka, inject

from src.application.dto.interaction import (
    InteractionDenied,
    InteractionPerformed,
    PerformInteractionCommand,
)
from src.application.use_cases.perform_interaction import PerformInteractionUseCase
from src.domain.exceptions import SelfInteraction
from src.domain.value_objects.interaction_type import InteractionType
from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId
from src.presentation.bot.texts import ru as texts

router = Router(name="interactions")


async def _handle(
    message: Message,
    kind: InteractionType,
    use_case: PerformInteractionUseCase,
) -> None:
    if message.from_user is None:
        return

    replied = message.reply_to_message
    if replied is None or replied.from_user is None or replied.from_user.is_bot:
        await message.reply(texts.interaction_needs_reply(kind))
        return

    actor = message.from_user
    target = replied.from_user

    try:
        result = await use_case.execute(
            PerformInteractionCommand(
                chat_id=TelegramChatId(message.chat.id),
                actor_tg_id=TelegramUserId(actor.id),
                actor_username=actor.username,
                target_tg_id=TelegramUserId(target.id),
                target_username=target.username,
                kind=kind,
            )
        )
    except SelfInteraction:
        await message.reply(texts.interaction_self())
        return

    if isinstance(result, InteractionDenied):
        await message.reply(texts.interaction_denied(result.kind, result.reason))
        return

    assert isinstance(result, InteractionPerformed)
    await message.reply(
        texts.interaction_done(
            kind=result.kind,
            actor_mention=texts.mention(actor.username, actor.id, actor.full_name),
            target_mention=texts.mention(target.username, target.id, target.full_name),
        )
    )


@router.message(Command("pet"))
@inject
async def handle_pet(
    message: Message,
    perform_interaction: FromDishka[PerformInteractionUseCase],
) -> None:
    await _handle(message, InteractionType.PET, perform_interaction)


@router.message(Command("kiss"))
@inject
async def handle_kiss(
    message: Message,
    perform_interaction: FromDishka[PerformInteractionUseCase],
) -> None:
    await _handle(message, InteractionType.KISS, perform_interaction)


@router.message(Command("fuck"))
@inject
async def handle_fuck(
    message: Message,
    perform_interaction: FromDishka[PerformInteractionUseCase],
) -> None:
    await _handle(message, InteractionType.FUCK, perform_interaction)
