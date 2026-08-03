from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from src.domain.value_objects.telegram_ids import TelegramChatId

DEFAULT_STAKE_CM = 5
BATTLE_EXPIRATION = timedelta(minutes=5)


class BattleStatus(str, Enum):
    PENDING = "pending"
    OPEN = "open"
    RESOLVED = "resolved"
    DECLINED = "declined"
    EXPIRED = "expired"


@dataclass(slots=True)
class Battle:
    id: int | None
    chat_id: TelegramChatId
    challenger_user_id: int
    opponent_user_id: int
    stake_cm: int
    status: BattleStatus
    winner_user_id: int | None
    created_at: datetime
    resolved_at: datetime | None

    @classmethod
    def new(
        cls,
        chat_id: TelegramChatId,
        challenger_user_id: int,
        opponent_user_id: int,
        stake_cm: int,
        now: datetime,
    ) -> Battle:
        return cls(
            id=None,
            chat_id=chat_id,
            challenger_user_id=challenger_user_id,
            opponent_user_id=opponent_user_id,
            stake_cm=stake_cm,
            status=BattleStatus.PENDING,
            winner_user_id=None,
            created_at=now,
            resolved_at=None,
        )

    def is_expired(self, now: datetime) -> bool:
        return (
            self.status is BattleStatus.PENDING
            and now - self.created_at > BATTLE_EXPIRATION
        )

    def decline(self, now: datetime) -> None:
        self.status = BattleStatus.DECLINED
        self.resolved_at = now

    def open_for_joining(self) -> None:
        """Opponent accepted — open a window during which others can join a side."""
        self.status = BattleStatus.OPEN

    def resolve(self, winner_user_id: int, now: datetime) -> None:
        self.status = BattleStatus.RESOLVED
        self.winner_user_id = winner_user_id
        self.resolved_at = now

    def expire(self, now: datetime) -> None:
        self.status = BattleStatus.EXPIRED
        self.resolved_at = now
