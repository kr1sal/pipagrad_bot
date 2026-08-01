from __future__ import annotations

from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from src.application.ports.telegram_gateway import BotAdmin
from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId
from src.infrastructure.telegram.pending_keyboards import (
    bot_battle_keyboard,
    orgy_keyboard,
)

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

    async def send_message(self, chat_id: TelegramChatId, text: str) -> None:
        await self._bot.send_message(chat_id=int(chat_id), text=text)

    async def announce_orgy(
        self, chat_id: TelegramChatId, text: str, event_id: int
    ) -> int:
        msg = await self._bot.send_message(
            chat_id=int(chat_id),
            text=text,
            reply_markup=orgy_keyboard(event_id=event_id, joined_count=0),
        )
        return msg.message_id

    async def announce_bot_battle(
        self,
        chat_id: TelegramChatId,
        text: str,
        event_id: int,
        other_label: str,
    ) -> int:
        msg = await self._bot.send_message(
            chat_id=int(chat_id),
            text=text,
            reply_markup=bot_battle_keyboard(
                event_id=event_id,
                pipa_count=0,
                other_count=0,
                other_label=other_label,
            ),
        )
        return msg.message_id

    async def update_orgy_join_count(
        self,
        chat_id: TelegramChatId,
        message_id: int,
        event_id: int,
        joined_count: int,
    ) -> None:
        try:
            await self._bot.edit_message_reply_markup(
                chat_id=int(chat_id),
                message_id=message_id,
                reply_markup=orgy_keyboard(
                    event_id=event_id, joined_count=joined_count
                ),
            )
        except TelegramBadRequest:
            pass  # unchanged, deleted, etc. — nothing to do

    async def update_bot_battle_counts(
        self,
        chat_id: TelegramChatId,
        message_id: int,
        event_id: int,
        pipa_count: int,
        other_count: int,
        other_label: str,
    ) -> None:
        try:
            await self._bot.edit_message_reply_markup(
                chat_id=int(chat_id),
                message_id=message_id,
                reply_markup=bot_battle_keyboard(
                    event_id=event_id,
                    pipa_count=pipa_count,
                    other_count=other_count,
                    other_label=other_label,
                ),
            )
        except TelegramBadRequest:
            pass

    async def finalize_message(
        self, chat_id: TelegramChatId, message_id: int, text: str
    ) -> None:
        try:
            await self._bot.edit_message_text(
                chat_id=int(chat_id),
                message_id=message_id,
                text=text,
                reply_markup=None,
            )
        except TelegramBadRequest:
            pass

    async def list_bot_admins(self, chat_id: TelegramChatId) -> list[BotAdmin]:
        try:
            me = await self._bot.me()
            admins = await self._bot.get_chat_administrators(chat_id=int(chat_id))
        except (TelegramBadRequest, TelegramForbiddenError):
            return []
        out: list[BotAdmin] = []
        for a in admins:
            u = a.user
            if not u.is_bot or u.id == me.id:
                continue
            out.append(
                BotAdmin(
                    tg_id=TelegramUserId(u.id),
                    username=u.username,
                    full_name=u.full_name,
                )
            )
        return out

    async def kick_user(
        self, chat_id: TelegramChatId, user_id: TelegramUserId
    ) -> bool:
        try:
            await self._bot.ban_chat_member(
                chat_id=int(chat_id), user_id=int(user_id)
            )
            return True
        except (TelegramBadRequest, TelegramForbiddenError):
            return False
