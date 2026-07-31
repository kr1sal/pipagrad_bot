from __future__ import annotations

from aiogram import Router
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message
from dishka.integrations.aiogram import FromDishka, inject

from src.application.dto.battle import (
    BattleDeclinedResult,
    BattleExpiredResult,
    BattleResolvedResult,
    ChallengeBattleCommand,
    RespondToBattleCommand,
)
from src.application.use_cases.challenge_battle import ChallengeBattleUseCase
from src.application.use_cases.respond_to_battle import RespondToBattleUseCase
from src.domain.entities.battle import DEFAULT_STAKE_CM
from src.domain.exceptions import (
    BattleNotFound,
    BattleNotPending,
    BattlesDisabled,
    InsufficientDickSize,
    NotYourBattle,
    SelfInteraction,
)
from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId
from src.presentation.bot.keyboards.battle import BattleCB, build as build_kb
from src.presentation.bot.texts import ru as texts

router = Router(name="battle")

_GROUP_TYPES = {ChatType.GROUP, ChatType.SUPERGROUP}


@router.message(Command("battle"))
@inject
async def handle_battle(
    message: Message,
    command: CommandObject,
    challenge: FromDishka[ChallengeBattleUseCase],
) -> None:
    if message.chat.type not in _GROUP_TYPES:
        await message.reply(texts.battle_only_in_groups())
        return

    if message.from_user is None:
        return

    replied = message.reply_to_message
    if replied is None or replied.from_user is None or replied.from_user.is_bot:
        await message.reply(texts.battle_needs_reply())
        return

    stake = DEFAULT_STAKE_CM
    if command.args:
        try:
            stake = int(command.args.strip().split()[0])
        except (ValueError, IndexError):
            await message.reply(texts.battle_bad_stake())
            return
        if stake < 1:
            await message.reply(texts.battle_bad_stake())
            return

    actor = message.from_user
    target = replied.from_user

    try:
        result = await challenge.execute(
            ChallengeBattleCommand(
                chat_id=TelegramChatId(message.chat.id),
                challenger_tg_id=TelegramUserId(actor.id),
                challenger_username=actor.username,
                opponent_tg_id=TelegramUserId(target.id),
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
    except InsufficientDickSize as e:
        await message.reply(texts.battle_insufficient(e.needed, e.actual))
        return

    await message.reply(
        texts.battle_challenge(
            challenger_mention=texts.mention(actor.username, actor.id, actor.full_name),
            opponent_mention=texts.mention(target.username, target.id, target.full_name),
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

    # Render outcome — replace the challenge message text and clear buttons
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
    elif isinstance(outcome, BattleResolvedResult):
        winner_is_actor = outcome.winner_tg_id == TelegramUserId(query.from_user.id)
        # We know the actor (opponent) — challenger we know only by tg_id.
        # For a nicer mention we'd need to fetch usernames; use plain id-mentions
        # for the other party.
        actor_mention = texts.mention(
            query.from_user.username, query.from_user.id, query.from_user.full_name
        )
        other_id = (
            outcome.loser_tg_id if winner_is_actor else outcome.winner_tg_id
        )
        other_mention = texts.mention(None, int(other_id))
        if winner_is_actor:
            winner_m, loser_m = actor_mention, other_mention
        else:
            winner_m, loser_m = other_mention, actor_mention
        await query.message.edit_text(
            texts.battle_resolved(
                winner_mention=winner_m,
                loser_mention=loser_m,
                stake_cm=outcome.stake_cm,
                winner_size_cm=outcome.winner_new_size_cm,
                loser_size_cm=outcome.loser_new_size_cm,
            )
        )
    await query.answer()
