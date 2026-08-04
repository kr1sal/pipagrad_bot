from __future__ import annotations

from aiogram import Router
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message
from dishka.integrations.aiogram import FromDishka, inject

from src.application.dto.battle import (
    BattleDeclinedResult,
    BattleExpiredResult,
    BattleOpenedResult,
    ChallengeBattleCommand,
    RespondToBattleCommand,
)
from src.application.use_cases.challenge_battle import ChallengeBattleUseCase
from src.application.use_cases.find_user_by_username import FindUserByUsernameUseCase
from src.application.use_cases.respond_to_battle import RespondToBattleUseCase
from src.domain.entities.battle import DEFAULT_STAKE_CM
from src.domain.entities.pending_event import TEAM_BATTLE_TIMER_MINUTES
from src.domain.exceptions import (
    BattleAlreadyActive,
    BattleNotFound,
    BattleNotPending,
    BattlesDisabled,
    InsufficientDickSize,
    NotYourBattle,
    SelfInteraction,
)
from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId
from src.infrastructure.telegram.pending_keyboards import team_battle_keyboard
from src.presentation.bot.handlers.target_resolution import resolve_target
from src.presentation.bot.keyboards.battle import BattleCB
from src.presentation.bot.keyboards.battle import build as build_kb
from src.presentation.bot.texts import ru as texts

router = Router(name="battle")

_GROUP_TYPES = {ChatType.GROUP, ChatType.SUPERGROUP}


@router.message(Command("battle"))
@inject
async def handle_battle(
    message: Message,
    command: CommandObject,
    challenge: FromDishka[ChallengeBattleUseCase],
    find_user: FromDishka[FindUserByUsernameUseCase],
) -> None:
    if message.chat.type not in _GROUP_TYPES:
        await message.reply(texts.battle_only_in_groups())
        return

    if message.from_user is None:
        return

    raw_username = None
    stake_tokens = []
    for token in command.args.strip().split() if command.args else []:
        if token.startswith("@") and raw_username is None:
            raw_username = token
        else:
            stake_tokens.append(token)

    target = await resolve_target(message, raw_username, find_user)
    if target is None:
        await message.reply(texts.battle_needs_reply())
        return
    if target.tg_id == 0:
        assert target.username is not None
        await message.reply(texts.interaction_user_not_found(target.username))
        return

    stake = DEFAULT_STAKE_CM
    if stake_tokens:
        try:
            stake = int(stake_tokens[0])
        except ValueError:
            await message.reply(texts.battle_bad_stake())
            return
        if stake < 1:
            await message.reply(texts.battle_bad_stake())
            return

    actor = message.from_user

    try:
        result = await challenge.execute(
            ChallengeBattleCommand(
                chat_id=TelegramChatId(message.chat.id),
                challenger_tg_id=TelegramUserId(actor.id),
                challenger_username=actor.username,
                opponent_tg_id=TelegramUserId(target.tg_id),
                opponent_username=target.username,
                stake_cm=stake,
            )
        )
    except SelfInteraction:
        await message.reply(texts.interaction_self())
        return
    except BattlesDisabled:
        await message.reply(texts.battles_disabled())
        return
    except BattleAlreadyActive:
        await message.reply(texts.battle_already_active())
        return
    except InsufficientDickSize as e:
        await message.reply(texts.battle_insufficient(e.needed, e.actual))
        return

    await message.reply(
        texts.battle_challenge(
            challenger_mention=texts.mention(actor.username, actor.id, actor.full_name),
            opponent_mention=texts.mention(
                target.username, target.tg_id, target.display_name
            ),
            stake_cm=result.stake_cm,
        ),
        reply_markup=build_kb(result.battle_id),
    )


@router.callback_query(BattleCB.filter())
@inject
async def cb_respond(
    query: CallbackQuery,
    callback_data: BattleCB,
    respond: FromDishka[RespondToBattleUseCase],
) -> None:
    if query.from_user is None or query.message is None:
        await query.answer()
        return

    try:
        outcome = await respond.execute(
            RespondToBattleCommand(
                battle_id=callback_data.battle_id,
                actor_tg_id=TelegramUserId(query.from_user.id),
                accept=callback_data.accept,
                chat_message_id=query.message.message_id,
            )
        )
    except NotYourBattle:
        await query.answer(texts.battle_not_your(), show_alert=True)
        return
    except BattleNotPending:
        await query.answer(texts.battle_not_pending(), show_alert=True)
        return
    except BattleNotFound:
        await query.answer("Не найдено.", show_alert=True)
        return
    except InsufficientDickSize as e:
        await query.answer(
            texts.battle_insufficient(e.needed, e.actual), show_alert=True
        )
        return

    # Render outcome — replace the challenge message text (and buttons, for
    # the terminal outcomes; BattleOpenedResult swaps in the join keyboard).
    if isinstance(outcome, BattleExpiredResult):
        await query.message.edit_text(texts.battle_expired())
    elif isinstance(outcome, BattleDeclinedResult):
        await query.message.edit_text(
            texts.battle_declined(
                opponent_mention=texts.mention(
                    query.from_user.username,
                    query.from_user.id,
                    query.from_user.full_name,
                )
            )
        )
    elif isinstance(outcome, BattleOpenedResult):
        # We know the actor (opponent) — challenger we know only by tg_id, so
        # their mention falls back to a plain id-link.
        opponent_mention = texts.mention(
            query.from_user.username, query.from_user.id, query.from_user.full_name
        )
        challenger_mention = texts.mention(None, int(outcome.challenger_tg_id))
        await query.message.edit_text(
            texts.battle_opened(
                challenger_mention=challenger_mention,
                opponent_mention=opponent_mention,
                stake_cm=outcome.stake_cm,
                minutes=TEAM_BATTLE_TIMER_MINUTES,
            ),
            reply_markup=team_battle_keyboard(
                event_id=outcome.pending_event_id,
                side1_count=1,
                side2_count=1,
                challenger_label=outcome.challenger_label,
                opponent_label=outcome.opponent_label,
            ),
        )
    await query.answer()
