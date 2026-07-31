from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime

from src.domain.value_objects.interaction_type import InteractionType
from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId

ALLOWED_RANDOM_EVENT_INTERVALS_MIN: tuple[int, ...] = (15, 30, 60, 120, 240)


@dataclass(frozen=True, slots=True)
class GroupSettings:
    battles_enabled: bool
    random_events_enabled: bool
    random_event_interval_minutes: int
    allowed_interactions: frozenset[InteractionType]

    @classmethod
    def default(cls) -> GroupSettings:
        return cls(
            battles_enabled=True,
            random_events_enabled=False,
            random_event_interval_minutes=60,
            allowed_interactions=frozenset(InteractionType),
        )

    def toggled_battles(self) -> GroupSettings:
        return replace(self, battles_enabled=not self.battles_enabled)

    def toggled_random_events(self) -> GroupSettings:
        return replace(self, random_events_enabled=not self.random_events_enabled)

    def toggled_interaction(self, kind: InteractionType) -> GroupSettings:
        allowed = set(self.allowed_interactions)
        if kind in allowed:
            allowed.remove(kind)
        else:
            allowed.add(kind)
        return replace(self, allowed_interactions=frozenset(allowed))

    def with_random_event_interval(self, minutes: int) -> GroupSettings:
        if minutes not in ALLOWED_RANDOM_EVENT_INTERVALS_MIN:
            raise ValueError(f"Interval {minutes} not in {ALLOWED_RANDOM_EVENT_INTERVALS_MIN}")
        return replace(self, random_event_interval_minutes=minutes)


@dataclass(slots=True)
class Group:
    chat_id: TelegramChatId
    title: str | None
    added_by_tg_id: TelegramUserId | None
    created_at: datetime
    settings: GroupSettings = field(default_factory=GroupSettings.default)
    last_random_event_at: datetime | None = None

    @classmethod
    def new(
        cls,
        chat_id: TelegramChatId,
        title: str | None,
        added_by_tg_id: TelegramUserId | None,
        now: datetime,
    ) -> Group:
        return cls(
            chat_id=chat_id,
            title=title,
            added_by_tg_id=added_by_tg_id,
            created_at=now,
            settings=GroupSettings.default(),
            last_random_event_at=None,
        )
