from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from dishka.integrations.aiogram import setup_dishka

from src.infrastructure.config.settings import Settings
from src.infrastructure.di.container import build_container
from src.presentation.bot.handlers.chat_member import router as chat_member_router
from src.presentation.bot.handlers.commands import router as commands_router
from src.presentation.bot.handlers.interactions import router as interactions_router
from src.presentation.bot.handlers.me import router as me_router
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
    dp.include_router(settings_router)
    dp.include_router(me_router)
    dp.include_router(interactions_router)
    dp.include_router(chat_member_router)

    setup_dishka(container=container, router=dp, auto_inject=True)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await container.close()


if __name__ == "__main__":
    asyncio.run(main())
