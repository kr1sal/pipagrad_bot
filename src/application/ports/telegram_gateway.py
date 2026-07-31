from __future__ import annotations

from typing import Protocol

from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId


class TelegramGateway(Protocol):
    async def is_chat_admin(
        self, chat_id: TelegramChatId, user_id: TelegramUserId
    ) -> bool: ...

    async def send_message(self, chat_id: TelegramChatId, text: str) -> None: ...
