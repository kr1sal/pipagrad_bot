from __future__ import annotations

import pytest

from src.domain.entities.group import (
    ALLOWED_RANDOM_EVENT_INTERVALS_MIN,
    GroupSettings,
)
from src.domain.value_objects.interaction_type import InteractionType


def test_defaults_are_permissive_except_random_events() -> None:
    s = GroupSettings.default()
    assert s.battles_enabled is True
    assert s.random_events_enabled is False
    assert s.allowed_interactions == frozenset(InteractionType)
    assert s.random_event_interval_minutes in ALLOWED_RANDOM_EVENT_INTERVALS_MIN


def test_toggle_battles_returns_new_instance() -> None:
    s = GroupSettings.default()
    s2 = s.toggled_battles()
    assert s.battles_enabled is True
    assert s2.battles_enabled is False
    assert s is not s2


def test_toggle_interaction_removes_and_adds_back() -> None:
    s = GroupSettings.default()
    s2 = s.toggled_interaction(InteractionType.FUCK)
    assert InteractionType.FUCK not in s2.allowed_interactions
    s3 = s2.toggled_interaction(InteractionType.FUCK)
    assert InteractionType.FUCK in s3.allowed_interactions


def test_set_interval_rejects_unlisted_value() -> None:
    s = GroupSettings.default()
    with pytest.raises(ValueError):
        s.with_random_event_interval(7)


def test_set_interval_accepts_listed_value() -> None:
    s = GroupSettings.default()
    s2 = s.with_random_event_interval(120)
    assert s2.random_event_interval_minutes == 120
