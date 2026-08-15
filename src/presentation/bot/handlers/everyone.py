from __future__ import annotations

import asyncio

from aiogram import Router
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from dishka.integrations.aiogram import FromDishka, inject

from src.application.use_cases.mention_everyone import MentionEveryoneUseCase
from src.domain.exceptions import NotAnAdmin
from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId
from src.presentation.bot.texts import ru as texts

router = Router(name="everyone")

_GROUP_TYPES = {ChatType.GROUP, ChatType.SUPERGROUP}


@router.message(Command("everyone", "all"))
@inject
async def handle_everyone(
    message: Message,
    command: CommandObject,
    mention_everyone: FromDishka[MentionEveryoneUseCase],
) -> None:
    if message.from_user is None:
        return
    if message.chat.type not in _GROUP_TYPES:
        await message.reply(texts.everyone_only_in_groups())
        return

    try:
        users = await mention_everyone.execute(
            TelegramChatId(message.chat.id),
            TelegramUserId(message.from_user.id),
        )
    except NotAnAdmin:
        await message.reply(texts.everyone_not_admin())
        return

    if not users:
        await message.reply(texts.everyone_empty())
        return

    note = command.args.strip() if command.args else None
    for chunk in texts.everyone_chunks(users, note):
        await message.answer(chunk)
        await asyncio.sleep(0.05)  # stay clear of Telegram's per-chat flood limit
