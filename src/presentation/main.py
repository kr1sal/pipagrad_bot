from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from dishka.integrations.aiogram import setup_dishka

from src.infrastructure.config.settings import Settings
from src.infrastructure.di.container import build_container
from src.infrastructure.scheduler.aps import RandomEventsScheduler
from src.presentation.bot.setup_commands import setup_bot_commands
from src.presentation.bot.handlers.battle import router as battle_router
from src.presentation.bot.handlers.chat_member import router as chat_member_router
from src.presentation.bot.handlers.commands import router as commands_router
from src.presentation.bot.handlers.everyone import router as everyone_router
from src.presentation.bot.handlers.gift import router as gift_router
from src.presentation.bot.handlers.history import router as history_router
from src.presentation.bot.handlers.inline import router as inline_router
from src.presentation.bot.handlers.interactions import router as interactions_router
from src.presentation.bot.handlers.me import router as me_router
from src.presentation.bot.handlers.pending import router as pending_router
from src.presentation.bot.handlers.pipacoin import router as pipacoin_router
from src.presentation.bot.handlers.settings import router as settings_router


async def main() -> None:
    settings = Settings()  # type: ignore[call-arg]
    logging.basicConfig(level=settings.log_level.upper())

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    container = build_container(settings, bot)

    dp = Dispatcher()
    dp.include_router(commands_router)
    dp.include_router(everyone_router)
    dp.include_router(settings_router)
    dp.include_router(me_router)
    dp.include_router(interactions_router)
    dp.include_router(gift_router)
    dp.include_router(history_router)
    dp.include_router(battle_router)
    dp.include_router(pending_router)
    dp.include_router(pipacoin_router)
    dp.include_router(inline_router)
    dp.include_router(chat_member_router)

    setup_dishka(container=container, router=dp, auto_inject=True)

    scheduler = RandomEventsScheduler(container)
    scheduler.start()

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await setup_bot_commands(bot)
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()
        await container.close()


if __name__ == "__main__":
    asyncio.run(main())
