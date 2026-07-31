from __future__ import annotations

from typing import Protocol

from src.domain.entities.dick import Dick
from src.domain.entities.group import Group, GroupSettings
from src.domain.entities.user import User
from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId


class UserRepository(Protocol):
    async def get_by_tg_id(self, tg_id: TelegramUserId) -> User | None: ...

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


class GroupRepository(Protocol):
    async def get(self, chat_id: TelegramChatId) -> Group | None: ...

    async def add(self, group: Group) -> Group: ...

    async def update_settings(
        self, chat_id: TelegramChatId, settings: GroupSettings
    ) -> None: ...
