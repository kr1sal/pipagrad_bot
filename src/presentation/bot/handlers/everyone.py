from __future__ import annotations

import asyncio
import re

from aiogram import F, Router
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

# Plain-text "@everyone" mention — Telegram never turns this into a real
# mention entity since there's no such user, so it just arrives as text.
# Matched anywhere in the message, not only at the start, since people
# tend to tack it onto a sentence rather than lead with it.
_EVERYONE_TOKEN_RE = re.compile(r"(?<!\w)@everyone(?!\w)", re.IGNORECASE)


async def _call_everyone(
    message: Message,
    note: str | None,
    mention_everyone: MentionEveryoneUseCase,
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

    for chunk in texts.everyone_chunks(users, note):
        await message.answer(chunk)
        await asyncio.sleep(0.05)  # stay clear of Telegram's per-chat flood limit


@router.message(Command("everyone", "all"))
@inject
async def handle_everyone(
    message: Message,
    command: CommandObject,
    mention_everyone: FromDishka[MentionEveryoneUseCase],
) -> None:
    note = command.args.strip() if command.args else None
    await _call_everyone(message, note, mention_everyone)


@router.message(F.text.regexp(_EVERYONE_TOKEN_RE))
@inject
async def handle_everyone_text(
    message: Message,
    mention_everyone: FromDishka[MentionEveryoneUseCase],
) -> None:
    assert message.text is not None
    note = _EVERYONE_TOKEN_RE.sub("", message.text).strip() or None
    await _call_everyone(message, note, mention_everyone)
