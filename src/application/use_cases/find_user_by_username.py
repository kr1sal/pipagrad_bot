from __future__ import annotations

from dataclasses import dataclass

from src.application.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.telegram_ids import TelegramUserId


@dataclass(frozen=True, slots=True)
class FoundUser:
    tg_id: TelegramUserId
    username: str


class FindUserByUsernameUseCase:
    """
    Looks up a user by Telegram username in the bot's own users table. Only
    finds people who've interacted with the bot at least once (that's how we
    got their username in the first place).
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def execute(self, username: str) -> FoundUser | None:
        cleaned = username.lstrip("@").strip()
        if not cleaned:
            return None
        async with self._uow as uow:
            user = await uow.users.get_by_username(cleaned)
            if user is None or user.username is None:
                return None
            return FoundUser(tg_id=user.tg_id, username=user.username)
