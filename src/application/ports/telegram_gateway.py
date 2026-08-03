from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId


@dataclass(frozen=True, slots=True)
class BotAdmin:
    tg_id: TelegramUserId
    username: str | None
    full_name: str


class TelegramGateway(Protocol):
    async def is_chat_admin(
        self, chat_id: TelegramChatId, user_id: TelegramUserId
    ) -> bool: ...

    async def send_message(self, chat_id: TelegramChatId, text: str) -> None: ...

    async def announce_orgy(
        self, chat_id: TelegramChatId, text: str, event_id: int
    ) -> int:
        """Send the orgy announcement with a Join button; returns message_id."""
        ...

    async def announce_bot_battle(
        self,
        chat_id: TelegramChatId,
        text: str,
        event_id: int,
        other_label: str,
    ) -> int:
        """Send the bot-battle announcement with two side buttons."""
        ...

    async def update_orgy_join_count(
        self,
        chat_id: TelegramChatId,
        message_id: int,
        event_id: int,
        joined_count: int,
    ) -> None: ...

    async def update_bot_battle_counts(
        self,
        chat_id: TelegramChatId,
        message_id: int,
        event_id: int,
        pipa_count: int,
        other_count: int,
        other_label: str,
    ) -> None: ...

    async def update_team_battle_counts(
        self,
        chat_id: TelegramChatId,
        message_id: int,
        event_id: int,
        side1_count: int,
        side2_count: int,
        challenger_label: str,
        opponent_label: str,
    ) -> None: ...

    async def finalize_message(
        self, chat_id: TelegramChatId, message_id: int, text: str
    ) -> None:
        """Replace a message's text and remove its inline keyboard."""
        ...

    async def list_bot_admins(
        self, chat_id: TelegramChatId
    ) -> list[BotAdmin]:
        """
        Return admin members that are bots, excluding self. Returns [] if the
        call fails or nobody qualifies.
        """
        ...

    async def kick_user(
        self, chat_id: TelegramChatId, user_id: TelegramUserId
    ) -> bool:
        """
        Ban the user from the chat. Returns True on success, False if we lack
        permission or the user can't be banned (creator, etc.).
        """
        ...
