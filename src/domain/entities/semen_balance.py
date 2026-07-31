from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.domain.value_objects.telegram_ids import TelegramChatId


@dataclass(frozen=True, slots=True)
class SemenConfig:
    cap_ml: int
    regen_per_hour: int
    fuck_cost_ml: int


@dataclass(slots=True)
class SemenBalance:
    """
    Per-user × per-chat semen reservoir. Persistence stores only the point-in-
    time balance and its timestamp; the "current" ml at any moment is projected
    lazily as `stored + elapsed_hours * regen`, capped at `cap`. This avoids a
    background job just to tick balances forward.
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
        config: SemenConfig,
        now: datetime,
    ) -> SemenBalance:
        # Start players at the cap so first-timers can act immediately.
        return cls(
            id=None,
            user_id=user_id,
            chat_id=chat_id,
            stored_ml=config.cap_ml,
            updated_at=now,
        )

    def current_ml(self, now: datetime, config: SemenConfig) -> int:
        elapsed_h = (now - self.updated_at).total_seconds() / 3600.0
        if elapsed_h < 0:
            elapsed_h = 0.0
        gained = int(elapsed_h * config.regen_per_hour)
        return min(config.cap_ml, self.stored_ml + gained)

    def try_spend(
        self, cost_ml: int, now: datetime, config: SemenConfig
    ) -> int | None:
        """
        Returns the new balance if `cost_ml` was successfully spent, or None if
        there wasn't enough — in the None case the entity is not mutated so the
        caller can safely inspect state and reject the operation.
        """
        current = self.current_ml(now, config)
        if current < cost_ml:
            return None
        self.stored_ml = current - cost_ml
        self.updated_at = now
        return self.stored_ml
