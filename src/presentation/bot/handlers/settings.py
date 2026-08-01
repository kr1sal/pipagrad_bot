from __future__ import annotations

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from dishka.integrations.aiogram import FromDishka, inject

from src.application.dto.group_settings import (
    SettingsChange,
    ToggleBattles,
    ToggleInteraction,
    ToggleRandomEvents,
    UpdateGroupSettingsCommand,
)
from src.application.use_cases.get_group_settings import GetGroupSettingsUseCase
from src.application.use_cases.update_group_settings import UpdateGroupSettingsUseCase
from src.domain.exceptions import NotAnAdmin
from src.domain.value_objects.interaction_type import InteractionType
from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId
from src.presentation.bot.keyboards.settings import SettingsCB, build as build_kb
from src.presentation.bot.texts import ru as texts

router = Router(name="settings")

_GROUP_TYPES = {ChatType.GROUP, ChatType.SUPERGROUP}


@router.message(Command("settings"))
@inject
async def handle_settings(
    message: Message,
    get_group_settings: FromDishka[GetGroupSettingsUseCase],
) -> None:
    if message.chat.type not in _GROUP_TYPES:
        await message.reply(texts.settings_only_in_groups())
        return
    group = await get_group_settings.execute(TelegramChatId(message.chat.id))
    await message.reply(
        texts.settings_header(),
        reply_markup=build_kb(group.settings),
        parse_mode="HTML",
    )


@router.callback_query(SettingsCB.filter(F.action == "tb"))
@inject
async def cb_toggle_battles(
    query: CallbackQuery,
    callback_data: SettingsCB,
    update_settings: FromDishka[UpdateGroupSettingsUseCase],
) -> None:
    await _apply(query, ToggleBattles(), update_settings)


@router.callback_query(SettingsCB.filter(F.action == "tre"))
@inject
async def cb_toggle_random_events(
    query: CallbackQuery,
    callback_data: SettingsCB,
    update_settings: FromDishka[UpdateGroupSettingsUseCase],
) -> None:
    await _apply(query, ToggleRandomEvents(), update_settings)


@router.callback_query(SettingsCB.filter(F.action == "ti"))
@inject
async def cb_toggle_interaction(
    query: CallbackQuery,
    callback_data: SettingsCB,
    update_settings: FromDishka[UpdateGroupSettingsUseCase],
) -> None:
    if callback_data.kind is None:
        await query.answer()
        return
    kind = InteractionType(callback_data.kind)
    await _apply(query, ToggleInteraction(kind=kind), update_settings)


async def _apply(
    query: CallbackQuery,
    change: SettingsChange,
    use_case: UpdateGroupSettingsUseCase,
) -> None:
    if query.from_user is None or query.message is None:
        await query.answer()
        return
    try:
        group = await use_case.execute(
            UpdateGroupSettingsCommand(
                chat_id=TelegramChatId(query.message.chat.id),
                actor_tg_id=TelegramUserId(query.from_user.id),
                change=change,
            )
        )
    except NotAnAdmin:
        await query.answer(texts.settings_not_admin(), show_alert=True)
        return

    await query.message.edit_reply_markup(reply_markup=build_kb(group.settings))
    await query.answer()
