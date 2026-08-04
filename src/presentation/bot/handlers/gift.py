from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from dishka.integrations.aiogram import FromDishka, inject

from src.application.dto.gift import GiftSizeCommand
from src.application.use_cases.find_user_by_username import FindUserByUsernameUseCase
from src.application.use_cases.gift_size import GiftSizeUseCase
from src.domain.exceptions import InsufficientDickSize, SelfInteraction
from src.domain.value_objects.telegram_ids import TelegramUserId
from src.presentation.bot.handlers.scope import resolve_scope_chat_id
from src.presentation.bot.handlers.target_resolution import resolve_target
from src.presentation.bot.texts import ru as texts

router = Router(name="gift")


@router.message(Command("gift"))
@inject
async def handle_gift(
    message: Message,
    command: CommandObject,
    gift_size: FromDishka[GiftSizeUseCase],
    find_user: FromDishka[FindUserByUsernameUseCase],
) -> None:
    if message.from_user is None:
        return

    parts = command.args.strip().split() if command.args else []

    try:
        amount = int(parts[0])
    except (ValueError, IndexError):
        await message.reply(texts.gift_bad_amount())
        return
    if amount < 1:
        await message.reply(texts.gift_bad_amount())
        return

    raw_username = parts[1] if len(parts) >= 2 else None
    target = await resolve_target(message, raw_username, find_user)
    if target is None:
        await message.reply(texts.gift_needs_target())
        return
    if target.tg_id == 0:
        assert target.username is not None
        await message.reply(texts.interaction_user_not_found(target.username))
        return

    actor = message.from_user

    try:
        result = await gift_size.execute(
            GiftSizeCommand(
                chat_id=resolve_scope_chat_id(message.chat),
                actor_tg_id=TelegramUserId(actor.id),
                actor_username=actor.username,
                target_tg_id=TelegramUserId(target.tg_id),
                target_username=target.username,
                amount_cm=amount,
            )
        )
    except SelfInteraction:
        await message.reply(texts.gift_self())
        return
    except InsufficientDickSize as e:
        await message.reply(texts.gift_insufficient(e.needed, e.actual))
        return

    await message.reply(
        texts.gift_done(
            actor_mention=texts.mention(actor.username, actor.id, actor.full_name),
            target_mention=texts.mention(
                target.username, target.tg_id, target.display_name
            ),
            amount_cm=result.amount_cm,
            actor_new_size_cm=result.actor_new_size_cm,
            target_new_size_cm=result.target_new_size_cm,
        )
    )
