from __future__ import annotations

from aiogram import Router
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from dishka.integrations.aiogram import FromDishka, inject

from src.application.dto.grow_dick import (
    GrowDickCommand,
    GrowDickCooldown,
    GrowDickResult,
)
from src.application.use_cases.get_chat_top import GetChatTopUseCase
from src.application.use_cases.grow_dick import GrowDickUseCase
from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId
from src.presentation.bot.texts import ru as texts

router = Router(name="commands")

_GROUP_TYPES = {ChatType.GROUP, ChatType.SUPERGROUP}


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    await message.answer(texts.start())


@router.message(Command("grow"))
@inject
async def handle_grow(
    message: Message,
    grow_dick: FromDishka[GrowDickUseCase],
) -> None:
    if message.from_user is None:
        return
    command = GrowDickCommand(
        tg_user_id=TelegramUserId(message.from_user.id),
        tg_username=message.from_user.username,
        chat_id=TelegramChatId(message.chat.id),
    )
    result = await grow_dick.execute(command)
    if isinstance(result, GrowDickCooldown):
        text = texts.grow_cooldown(result.remaining, result.current_size_cm)
    elif isinstance(result, GrowDickResult):
        text = texts.grow_success(result.delta_cm, result.new_size_cm)
    else:  # pragma: no cover
        text = "?"
    await message.reply(text)


@router.message(Command("top"))
@inject
async def handle_top(
    message: Message,
    get_top: FromDishka[GetChatTopUseCase],
) -> None:
    if message.chat.type not in _GROUP_TYPES:
        await message.reply(texts.top_only_in_groups())
        return
    entries = await get_top.execute(TelegramChatId(message.chat.id), limit=10)
    if not entries:
        await message.reply(texts.top_empty())
        return
    lines = [texts.top_header()]
    for e in entries:
        lines.append(
            texts.top_line(
                rank=e.rank,
                mention=texts.mention(e.username, int(e.tg_id)),
                size_cm=e.size_cm,
            )
        )
    await message.reply("\n".join(lines))
