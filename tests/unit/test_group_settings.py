from __future__ import annotations

from src.domain.entities.group import GroupSettings
from src.domain.value_objects.interaction_type import InteractionType


def test_defaults_are_permissive_except_random_events() -> None:
    s = GroupSettings.default()
    assert s.battles_enabled is True
    assert s.random_events_enabled is False
    assert s.allowed_interactions == frozenset(InteractionType)


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
