from __future__ import annotations

from aiogram.enums import ChatType
from aiogram.types import Chat

from src.domain.value_objects.telegram_ids import GLOBAL_CHAT_ID, TelegramChatId


def resolve_scope_chat_id(chat: Chat) -> TelegramChatId:
    """
    Private chats with the bot share the global scope with inline-mode
    interactions (one dick/semen per user, everywhere). Groups and
    supergroups keep their own local scope, per chat.
    """
    if chat.type == ChatType.PRIVATE:
        return GLOBAL_CHAT_ID
    return TelegramChatId(chat.id)
