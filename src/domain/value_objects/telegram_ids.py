from __future__ import annotations

from dataclasses import dataclass
from typing import NewType

TelegramUserId = NewType("TelegramUserId", int)
TelegramChatId = NewType("TelegramChatId", int)

# Reserved chat id for the "global" scope: DMs with the bot and inline-mode
# interactions all share this one bucket per user, instead of each real chat
# having its own. Real Telegram chats never use 0 (private chats use the
# user's own positive tg_id, groups/supergroups use negative ids), so this
# can't collide with a live chat.
GLOBAL_CHAT_ID = TelegramChatId(0)


@dataclass(frozen=True, slots=True)
class UserRef:
    tg_id: TelegramUserId
    username: str | None
