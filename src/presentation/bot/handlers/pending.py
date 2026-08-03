from __future__ import annotations

from aiogram import Router
from aiogram.types import CallbackQuery
from dishka.integrations.aiogram import FromDishka, inject

from src.application.ports.telegram_gateway import TelegramGateway
from src.application.use_cases.join_pending import (
    JoinBotBattleUseCase,
    JoinOrgyUseCase,
    JoinResult,
    JoinTeamBattleUseCase,
)
from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId
from src.infrastructure.telegram.pending_keyboards import (
    BotBattleCB,
    OrgyCB,
    TeamBattleCB,
)
from src.presentation.bot.texts import ru as texts

router = Router(name="pending")


@router.callback_query(OrgyCB.filter())
@inject
async def cb_join_orgy(
    query: CallbackQuery,
    callback_data: OrgyCB,
    join: FromDishka[JoinOrgyUseCase],
    telegram: FromDishka[TelegramGateway],
) -> None:
    if query.from_user is None or query.message is None:
        await query.answer()
        return

    result, counts = await join.execute(
        event_id=callback_data.event_id,
        actor_tg_id=TelegramUserId(query.from_user.id),
        actor_username=query.from_user.username,
    )

    if result is JoinResult.NOT_FOUND:
        await query.answer(texts.pending_not_found(), show_alert=True)
        return

    assert counts is not None
    toast = (
        texts.orgy_toast_joined()
        if result is JoinResult.JOINED
        else texts.orgy_toast_left()
    )
    await telegram.update_orgy_join_count(
        chat_id=TelegramChatId(query.message.chat.id),
        message_id=query.message.message_id,
        event_id=callback_data.event_id,
        joined_count=counts.joined_count,
    )
    await query.answer(toast)


@router.callback_query(BotBattleCB.filter())
@inject
async def cb_join_bot_battle(
    query: CallbackQuery,
    callback_data: BotBattleCB,
    join: FromDishka[JoinBotBattleUseCase],
    telegram: FromDishka[TelegramGateway],
) -> None:
    if query.from_user is None or query.message is None:
        await query.answer()
        return

    result, counts = await join.execute(
        event_id=callback_data.event_id,
        actor_tg_id=TelegramUserId(query.from_user.id),
        actor_username=query.from_user.username,
        side=callback_data.side,
    )

    if result is JoinResult.NOT_FOUND:
        await query.answer(texts.pending_not_found(), show_alert=True)
        return
    if result is JoinResult.ALREADY_ON_OTHER_SIDE:
        await query.answer(texts.bot_battle_not_your_side(), show_alert=True)
        return

    assert counts is not None
    side_label = "Pipagrad" if callback_data.side == "pipa" else counts.other_label
    await telegram.update_bot_battle_counts(
        chat_id=TelegramChatId(query.message.chat.id),
        message_id=query.message.message_id,
        event_id=callback_data.event_id,
        pipa_count=counts.pipa_count,
        other_count=counts.other_count,
        other_label=counts.other_label,
    )
    await query.answer(texts.bot_battle_toast_side(side_label))


@router.callback_query(TeamBattleCB.filter())
@inject
async def cb_join_team_battle(
    query: CallbackQuery,
    callback_data: TeamBattleCB,
    join: FromDishka[JoinTeamBattleUseCase],
    telegram: FromDishka[TelegramGateway],
) -> None:
    if query.from_user is None or query.message is None:
        await query.answer()
        return

    result, counts = await join.execute(
        event_id=callback_data.event_id,
        actor_tg_id=TelegramUserId(query.from_user.id),
        actor_username=query.from_user.username,
        side=callback_data.side,
    )

    if result is JoinResult.NOT_FOUND:
        await query.answer(texts.pending_not_found(), show_alert=True)
        return
    if result is JoinResult.ALREADY_ON_OTHER_SIDE:
        await query.answer(texts.bot_battle_not_your_side(), show_alert=True)
        return

    assert counts is not None
    side_label = (
        counts.challenger_label if callback_data.side == 1 else counts.opponent_label
    )
    await telegram.update_team_battle_counts(
        chat_id=TelegramChatId(query.message.chat.id),
        message_id=query.message.message_id,
        event_id=callback_data.event_id,
        side1_count=counts.side1_count,
        side2_count=counts.side2_count,
        challenger_label=counts.challenger_label,
        opponent_label=counts.opponent_label,
    )
    await query.answer(texts.bot_battle_toast_side(side_label))
