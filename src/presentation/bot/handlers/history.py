from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from dishka.integrations.aiogram import FromDishka, inject

from src.application.use_cases.get_dick_history import GetDickHistoryUseCase
from src.domain.value_objects.telegram_ids import TelegramUserId
from src.presentation.bot.handlers.scope import resolve_scope_chat_id
from src.presentation.bot.keyboards.history import HistoryCB
from src.presentation.bot.keyboards.history import build as build_kb
from src.presentation.bot.texts import ru as texts

router = Router(name="history")


@router.message(Command("history"))
@inject
async def handle_history(
    message: Message,
    get_history: FromDishka[GetDickHistoryUseCase],
) -> None:
    if message.from_user is None:
        return
    page = await get_history.execute(
        TelegramUserId(message.from_user.id),
        resolve_scope_chat_id(message.chat),
    )
    await message.reply(
        texts.history_page(page),
        reply_markup=build_kb(page.page, page.has_prev, page.has_next),
    )


@router.callback_query(HistoryCB.filter())
@inject
async def cb_history_page(
    query: CallbackQuery,
    callback_data: HistoryCB,
    get_history: FromDishka[GetDickHistoryUseCase],
) -> None:
    if query.from_user is None or query.message is None:
        await query.answer()
        return
    page = await get_history.execute(
        TelegramUserId(query.from_user.id),
        resolve_scope_chat_id(query.message.chat),
        page=callback_data.page,
    )
    await query.message.edit_text(
        texts.history_page(page),
        reply_markup=build_kb(page.page, page.has_prev, page.has_next),
    )
    await query.answer()
