from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message
from dishka.integrations.aiogram import FromDishka, inject

from src.application.dto.pipacoin import ExchangeSizeCommand, TransferPipaCoinCommand
from src.application.use_cases.exchange_size import ExchangeSizeUseCase
from src.application.use_cases.find_user_by_username import FindUserByUsernameUseCase
from src.application.use_cases.get_pipacoin_history import GetPipaCoinHistoryUseCase
from src.application.use_cases.get_pipacoin_wallet import GetPipaCoinWalletUseCase
from src.application.use_cases.transfer_pipacoin import TransferPipaCoinUseCase
from src.domain.exceptions import (
    InsufficientDickSize,
    InsufficientPipaCoinBalance,
    SelfInteraction,
)
from src.domain.value_objects.telegram_ids import TelegramUserId
from src.presentation.bot.handlers.scope import resolve_scope_chat_id
from src.presentation.bot.handlers.target_resolution import resolve_target
from src.presentation.bot.keyboards.pipacoin_history import PipaHistoryCB
from src.presentation.bot.keyboards.pipacoin_history import build as build_kb
from src.presentation.bot.texts import ru as texts

router = Router(name="pipacoin")


@router.message(Command("wallet"))
@inject
async def handle_wallet(
    message: Message,
    get_wallet: FromDishka[GetPipaCoinWalletUseCase],
) -> None:
    if message.from_user is None:
        return
    balance = await get_wallet.execute(TelegramUserId(message.from_user.id))
    await message.reply(texts.wallet_balance(balance))


@router.message(Command("exchange"))
@inject
async def handle_exchange(
    message: Message,
    command: CommandObject,
    exchange_size: FromDishka[ExchangeSizeUseCase],
) -> None:
    if message.from_user is None:
        return

    parts = command.args.strip().split() if command.args else []
    try:
        amount = int(parts[0])
    except (ValueError, IndexError):
        await message.reply(texts.exchange_bad_amount())
        return
    if amount < 1:
        await message.reply(texts.exchange_bad_amount())
        return

    actor = message.from_user
    try:
        result = await exchange_size.execute(
            ExchangeSizeCommand(
                tg_user_id=TelegramUserId(actor.id),
                tg_username=actor.username,
                chat_id=resolve_scope_chat_id(message.chat),
                amount_cm=amount,
            )
        )
    except InsufficientDickSize as e:
        await message.reply(texts.exchange_insufficient(e.needed, e.actual))
        return

    await message.reply(
        texts.exchange_done(
            spent_cm=result.spent_cm,
            gained_pipacoin=result.gained_pipacoin,
            new_size_cm=result.new_size_cm,
            new_balance=result.new_balance,
        )
    )


@router.message(Command("pay"))
@inject
async def handle_pay(
    message: Message,
    command: CommandObject,
    transfer: FromDishka[TransferPipaCoinUseCase],
    find_user: FromDishka[FindUserByUsernameUseCase],
) -> None:
    if message.from_user is None:
        return

    parts = command.args.strip().split() if command.args else []
    try:
        amount = int(parts[0])
    except (ValueError, IndexError):
        await message.reply(texts.pay_bad_amount())
        return
    if amount < 1:
        await message.reply(texts.pay_bad_amount())
        return

    raw_username = parts[1] if len(parts) >= 2 else None
    target = await resolve_target(message, raw_username, find_user)
    if target is None:
        await message.reply(texts.pay_needs_target())
        return
    if target.tg_id == 0:
        assert target.username is not None
        await message.reply(texts.interaction_user_not_found(target.username))
        return

    actor = message.from_user
    try:
        result = await transfer.execute(
            TransferPipaCoinCommand(
                actor_tg_id=TelegramUserId(actor.id),
                actor_username=actor.username,
                target_tg_id=TelegramUserId(target.tg_id),
                target_username=target.username,
                amount=amount,
            )
        )
    except SelfInteraction:
        await message.reply(texts.pay_self())
        return
    except InsufficientPipaCoinBalance as e:
        await message.reply(texts.pay_insufficient(e.needed, e.actual))
        return

    await message.reply(
        texts.pay_done(
            actor_mention=texts.mention(actor.username, actor.id, actor.full_name),
            target_mention=texts.mention(
                target.username, target.tg_id, target.display_name
            ),
            amount=result.amount,
            actor_new_balance=result.actor_new_balance,
            target_new_balance=result.target_new_balance,
        )
    )


@router.message(Command("pipahistory"))
@inject
async def handle_pipahistory(
    message: Message,
    get_history: FromDishka[GetPipaCoinHistoryUseCase],
) -> None:
    if message.from_user is None:
        return
    page = await get_history.execute(TelegramUserId(message.from_user.id))
    await message.reply(
        texts.pipacoin_history_page(page),
        reply_markup=build_kb(page.page, page.has_prev, page.has_next),
    )


@router.callback_query(PipaHistoryCB.filter())
@inject
async def cb_pipahistory_page(
    query: CallbackQuery,
    callback_data: PipaHistoryCB,
    get_history: FromDishka[GetPipaCoinHistoryUseCase],
) -> None:
    if query.from_user is None or query.message is None:
        await query.answer()
        return
    page = await get_history.execute(
        TelegramUserId(query.from_user.id), page=callback_data.page
    )
    await query.message.edit_text(
        texts.pipacoin_history_page(page),
        reply_markup=build_kb(page.page, page.has_prev, page.has_next),
    )
    await query.answer()
