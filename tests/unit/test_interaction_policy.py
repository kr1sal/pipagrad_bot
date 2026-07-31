from __future__ import annotations

from src.domain.entities.group import GroupSettings
from src.domain.services.interaction_policy import Denial, check
from src.domain.value_objects.interaction_type import InteractionType
from src.domain.value_objects.user_preferences import UserPreferences


def test_allowed_when_group_and_target_both_permit() -> None:
    assert (
        check(InteractionType.KISS, GroupSettings.default(), UserPreferences.default())
        is None
    )


def test_denied_by_group_takes_precedence_over_target() -> None:
    group = GroupSettings.default().toggled_interaction(InteractionType.FUCK)
    # target also denies — but group wins
    target = UserPreferences.default().toggled(InteractionType.FUCK)
    assert check(InteractionType.FUCK, group, target) is Denial.BY_GROUP


def test_denied_by_target_when_group_allows() -> None:
    group = GroupSettings.default()
    target = UserPreferences.default().toggled(InteractionType.PET)
    assert check(InteractionType.PET, group, target) is Denial.BY_TARGET
