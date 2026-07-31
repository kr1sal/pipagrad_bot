from __future__ import annotations

from dataclasses import dataclass
from typing import NewType

TelegramUserId = NewType("TelegramUserId", int)
TelegramChatId = NewType("TelegramChatId", int)


@dataclass(frozen=True, slots=True)
class UserRef:
    tg_id: TelegramUserId
    username: str | None
