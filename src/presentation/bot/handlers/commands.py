from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from dishka.integrations.aiogram import FromDishka, inject

from src.application.dto.grow_dick import (
    GrowDickCommand,
    GrowDickCooldown,
    GrowDickResult,
)
from src.application.use_cases.get_top import GetTopUseCase
from src.application.use_cases.grow_dick import GrowDickUseCase
from src.domain.value_objects.telegram_ids import GLOBAL_CHAT_ID, TelegramUserId
from src.presentation.bot.handlers.scope import resolve_scope_chat_id
from src.presentation.bot.texts import ru as texts

router = Router(name="commands")


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
        chat_id=resolve_scope_chat_id(message.chat),
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
    get_top: FromDishka[GetTopUseCase],
) -> None:
    chat_id = resolve_scope_chat_id(message.chat)
    entries = await get_top.execute(chat_id, limit=10)
    if not entries:
        await message.reply(texts.top_empty())
        return
    lines = [texts.top_header(is_global=chat_id == GLOBAL_CHAT_ID)]
    for e in entries:
        lines.append(
            texts.top_line(
                rank=e.rank,
                mention=texts.mention(e.username, int(e.tg_id)),
                size_cm=e.size_cm,
            )
        )
    await message.reply("\n".join(lines))
