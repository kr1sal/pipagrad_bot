from __future__ import annotations

from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId

_ADMIN_STATUSES = {ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR}


class AiogramTelegramGateway:
    def __init__(self, bot: Bot) -> None:
        self._bot = bot

    async def is_chat_admin(
        self, chat_id: TelegramChatId, user_id: TelegramUserId
    ) -> bool:
        try:
            member = await self._bot.get_chat_member(
                chat_id=int(chat_id), user_id=int(user_id)
            )
        except (TelegramBadRequest, TelegramForbiddenError):
            return False
        return member.status in _ADMIN_STATUSES
