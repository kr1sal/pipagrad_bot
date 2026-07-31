from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from dishka.integrations.aiogram import setup_dishka

from src.infrastructure.config.settings import Settings
from src.infrastructure.di.container import build_container
from src.presentation.bot.handlers.commands import router as commands_router


async def main() -> None:
    settings = Settings()  # type: ignore[call-arg]
    logging.basicConfig(level=settings.log_level.upper())

    container = build_container(settings)

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.include_router(commands_router)

    setup_dishka(container=container, router=dp, auto_inject=True)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await container.close()


if __name__ == "__main__":
    asyncio.run(main())
