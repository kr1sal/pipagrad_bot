from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.domain.value_objects.telegram_ids import TelegramChatId


@dataclass(frozen=True, slots=True)
class SemenConfig:
    base_cap_ml: int
    cap_per_cm: int
    regen_per_hour: int
    fuck_cost_ml: int

    def cap_for(self, dick_size_cm: int) -> int:
        """
        The bigger the dick, the higher the ceiling. Linear so behavior stays
        predictable and admins can reason about it without a spreadsheet.
        """
        if dick_size_cm < 0:
            dick_size_cm = 0
        return self.base_cap_ml + dick_size_cm * self.cap_per_cm


@dataclass(slots=True)
class SemenBalance:
    """
    Per-user × per-chat semen reservoir. Persistence stores only the point-in-
    time balance and its timestamp; the "current" ml at any moment is projected
    lazily as `stored + elapsed_hours * regen`, capped at the caller-supplied
    `cap_ml`. The cap is passed in per call (rather than stored on the config)
    because it depends on live dick size, which the entity intentionally
    doesn't know about.
    """

    id: int | None
    user_id: int
    chat_id: TelegramChatId
    stored_ml: int
    updated_at: datetime

    @classmethod
    def initial(
        cls,
        user_id: int,
        chat_id: TelegramChatId,
        initial_ml: int,
        now: datetime,
    ) -> SemenBalance:
        return cls(
            id=None,
            user_id=user_id,
            chat_id=chat_id,
            stored_ml=initial_ml,
            updated_at=now,
        )

    def current_ml(
        self, now: datetime, regen_per_hour: int, cap_ml: int
    ) -> int:
        elapsed_h = (now - self.updated_at).total_seconds() / 3600.0
        if elapsed_h < 0:
            elapsed_h = 0.0
        gained = int(elapsed_h * regen_per_hour)
        return min(cap_ml, self.stored_ml + gained)

    def try_spend(
        self,
        cost_ml: int,
        now: datetime,
        regen_per_hour: int,
        cap_ml: int,
    ) -> int | None:
        """
        Returns the new balance if `cost_ml` was successfully spent, or None if
        there wasn't enough — in the None case the entity is not mutated so the
        caller can safely inspect state and reject the operation.
        """
        current = self.current_ml(now, regen_per_hour, cap_ml)
        if current < cost_ml:
            return None
        self.stored_ml = current - cost_ml
        self.updated_at = now
        return self.stored_ml
