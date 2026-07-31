from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from dishka.integrations.aiogram import FromDishka, inject

from src.application.dto.grow_dick import (
    GrowDickCommand,
    GrowDickCooldown,
    GrowDickResult,
)
from src.application.use_cases.grow_dick import GrowDickUseCase
from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId
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
