from __future__ import annotations

from aiogram import Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from dishka.integrations.aiogram import FromDishka, inject

from src.application.dto.interaction import (
    GetMyPreferencesCommand,
    ToggleMyPreferenceCommand,
)
from src.application.use_cases.get_my_chat_balance import GetMyChatBalanceUseCase
from src.application.use_cases.get_my_preferences import GetMyPreferencesUseCase
from src.application.use_cases.toggle_my_preference import ToggleMyPreferenceUseCase
from src.domain.value_objects.interaction_type import InteractionType
from src.domain.value_objects.telegram_ids import GLOBAL_CHAT_ID, TelegramUserId
from src.presentation.bot.handlers.scope import resolve_scope_chat_id
from src.presentation.bot.keyboards.me import PrefsCB, build as build_kb
from src.presentation.bot.texts import ru as texts

router = Router(name="me")

_ALLOWED_TYPES = {ChatType.GROUP, ChatType.SUPERGROUP, ChatType.PRIVATE}


@router.message(Command("me"))
@inject
async def handle_me(
    message: Message,
    get_prefs: FromDishka[GetMyPreferencesUseCase],
    get_balance: FromDishka[GetMyChatBalanceUseCase],
) -> None:
    if message.chat.type not in _ALLOWED_TYPES:
        await message.reply(texts.me_unsupported_here())
        return
    if message.from_user is None:
        return
    tg_user_id = TelegramUserId(message.from_user.id)
    chat_id = resolve_scope_chat_id(message.chat)
    prefs = await get_prefs.execute(
        GetMyPreferencesCommand(
            tg_user_id=tg_user_id,
            tg_username=message.from_user.username,
            chat_id=chat_id,
        )
    )
    balance = await get_balance.execute(tg_user_id, chat_id)
    await message.reply(
        texts.me_header(balance, is_global=chat_id == GLOBAL_CHAT_ID),
        reply_markup=build_kb(prefs),
    )


@router.callback_query(PrefsCB.filter())
@inject
async def cb_toggle_pref(
    query: CallbackQuery,
    callback_data: PrefsCB,
    toggle: FromDishka[ToggleMyPreferenceUseCase],
) -> None:
    if query.from_user is None or query.message is None:
        await query.answer()
        return
    # /me menu is scoped to whoever ran /me — it's a reply to their command.
    owner = getattr(query.message, "reply_to_message", None)
    if owner and owner.from_user and owner.from_user.id != query.from_user.id:
        await query.answer("Это не твоё меню — нажми /me сам(-а).", show_alert=True)
        return
    kind = InteractionType(callback_data.kind)
    prefs = await toggle.execute(
        ToggleMyPreferenceCommand(
            tg_user_id=TelegramUserId(query.from_user.id),
            tg_username=query.from_user.username,
            chat_id=resolve_scope_chat_id(query.message.chat),
            kind=kind,
        )
    )
    await query.message.edit_reply_markup(reply_markup=build_kb(prefs))
    await query.answer()
