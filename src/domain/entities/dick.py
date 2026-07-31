from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from src.domain.exceptions import CooldownActive
from src.domain.value_objects.dick_size import DickSize
from src.domain.value_objects.telegram_ids import TelegramChatId


@dataclass(slots=True)
class Dick:
    """
    Per-chat dick of a specific user. Size and last_grow_at are chat-scoped so that
    the same user has independent stats in different groups.
    """

    id: int | None
    user_id: int
    chat_id: TelegramChatId
    size: DickSize
    last_grow_at: datetime | None

    @classmethod
    def initial(cls, user_id: int, chat_id: TelegramChatId) -> Dick:
        return cls(
            id=None,
            user_id=user_id,
            chat_id=chat_id,
            size=DickSize(0),
            last_grow_at=None,
        )

    def grow(self, delta_cm: int, now: datetime, cooldown: timedelta) -> int:
        """
        Apply a growth delta if the cooldown has elapsed.
        Returns the actual applied delta (clamped by DickSize bounds).
        Raises CooldownActive if the cooldown has not yet elapsed.
        """
        if self.last_grow_at is not None:
            elapsed = now - self.last_grow_at
            if elapsed < cooldown:
                raise CooldownActive(cooldown - elapsed)

        old = self.size
        self.size = old.apply(delta_cm)
        self.last_grow_at = now
        return self.size.cm - old.cm
