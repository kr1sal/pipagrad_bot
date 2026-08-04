from __future__ import annotations

from datetime import datetime
from typing import Protocol

from src.domain.entities.battle import Battle
from src.domain.entities.dick import Dick
from src.domain.entities.group import Group, GroupSettings
from src.domain.entities.pending_event import PendingEvent
from src.domain.entities.semen_balance import SemenBalance
from src.domain.entities.user import User
from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId
from src.domain.value_objects.user_preferences import UserPreferences


class UserRepository(Protocol):
    async def get_by_tg_id(self, tg_id: TelegramUserId) -> User | None: ...

    async def get_by_id(self, user_id: int) -> User | None: ...

    async def get_by_username(self, username: str) -> User | None:
        """Case-insensitive lookup — Telegram usernames are case-insensitive."""
        ...

    async def add(self, user: User) -> User:
        """Persist a new user and return it with the assigned id."""
        ...


class DickRepository(Protocol):
    async def get(
        self, user_id: int, chat_id: TelegramChatId
    ) -> Dick | None: ...

    async def add(self, dick: Dick) -> Dick:
        """Persist a new dick and return it with the assigned id."""
        ...

    async def update(self, dick: Dick) -> None: ...

    async def list_for_chat(self, chat_id: TelegramChatId) -> list[Dick]: ...

    async def list_top_for_chat(
        self, chat_id: TelegramChatId, limit: int
    ) -> list[Dick]: ...


class GroupRepository(Protocol):
    async def get(self, chat_id: TelegramChatId) -> Group | None: ...

    async def add(self, group: Group) -> Group: ...

    async def update_settings(
        self, chat_id: TelegramChatId, settings: GroupSettings
    ) -> None: ...

    async def list_with_random_events_ready(
        self, now: datetime
    ) -> list[Group]: ...

    async def mark_random_event_fired(
        self, chat_id: TelegramChatId, next_at: datetime
    ) -> None:
        """Set the next-fire time for random events; earlier ones become eligible."""
        ...


class UserPreferencesRepository(Protocol):
    async def get(
        self, user_id: int, chat_id: TelegramChatId
    ) -> UserPreferences | None: ...

    async def upsert(
        self,
        user_id: int,
        chat_id: TelegramChatId,
        prefs: UserPreferences,
    ) -> None: ...


class BattleRepository(Protocol):
    async def add(self, battle: Battle) -> Battle: ...

    async def get(self, battle_id: int) -> Battle | None: ...

    async def update(self, battle: Battle) -> None: ...

    async def get_active_between(
        self, chat_id: TelegramChatId, user_a_id: int, user_b_id: int
    ) -> Battle | None:
        """An unresolved (pending/open) battle between this pair, if any."""
        ...


class PendingEventRepository(Protocol):
    async def add(self, event: PendingEvent) -> PendingEvent: ...

    async def get(
        self, event_id: int, *, for_update: bool = False
    ) -> PendingEvent | None: ...

    async def list_ready(self, now: datetime) -> list[PendingEvent]: ...

    async def update_payload(
        self, event_id: int, payload: dict[str, object]
    ) -> None: ...

    async def set_message_id(
        self, event_id: int, chat_message_id: int
    ) -> None: ...

    async def delete(self, event_id: int) -> None: ...


class SemenBalanceRepository(Protocol):
    async def get(
        self, user_id: int, chat_id: TelegramChatId
    ) -> SemenBalance | None: ...

    async def upsert(self, balance: SemenBalance) -> SemenBalance:
        """Insert or update; returns the entity with `id` populated on insert."""
        ...
