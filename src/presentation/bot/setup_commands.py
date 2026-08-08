from __future__ import annotations

from aiogram import Bot
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeDefault,
)

# Commands that make sense everywhere.
_UNIVERSAL: tuple[BotCommand, ...] = (
    BotCommand(command="start", description="Что это такое"),
    BotCommand(command="top", description="Глобальный топ по максимуму"),
    BotCommand(command="grow", description="Вырастить писюнчик (раз в сутки)"),
    BotCommand(command="history", description="История изменений см"),
    BotCommand(command="wallet", description="Баланс PipaCoin"),
    BotCommand(command="exchange", description="Обменять см на PipaCoin: /exchange см"),
    BotCommand(command="pay", description="Перевести PipaCoin: /pay сумма @username"),
    BotCommand(command="pipahistory", description="История операций с PipaCoin"),
)

# Commands that only work in groups. They need reply/target/chat context.
_GROUP_ONLY: tuple[BotCommand, ...] = (
    BotCommand(command="me", description="Мои разрешения в этом чате"),
    BotCommand(command="pet", description="Погладить (reply или @username)"),
    BotCommand(command="kiss", description="Поцеловать (reply или @username)"),
    BotCommand(command="hug", description="Обнять (reply или @username)"),
    BotCommand(command="fuck", description="Трахнуть (reply или @username)"),
    BotCommand(command="gift", description="Подарить см писюна: /gift см (reply или @username)"),
    BotCommand(command="battle", description="Битва: /battle [ставка] (reply или @username)"),
    BotCommand(command="settings", description="Настройки чата (только админы)"),
)


async def setup_bot_commands(bot: Bot) -> None:
    """
    Publishes the blue-`/`-button menu. Private chats hide group-only commands;
    groups get the full set. Default scope is a safety net for chat types not
    covered explicitly.
    """
    await bot.set_my_commands(
        list(_UNIVERSAL), scope=BotCommandScopeAllPrivateChats()
    )
    await bot.set_my_commands(
        list(_UNIVERSAL + _GROUP_ONLY), scope=BotCommandScopeAllGroupChats()
    )
    await bot.set_my_commands(
        list(_UNIVERSAL + _GROUP_ONLY), scope=BotCommandScopeDefault()
    )
