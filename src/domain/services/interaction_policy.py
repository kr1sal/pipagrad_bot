from __future__ import annotations

from enum import Enum

from src.domain.entities.group import GroupSettings
from src.domain.value_objects.interaction_type import InteractionType
from src.domain.value_objects.user_preferences import UserPreferences


class Denial(str, Enum):
    """Reason an interaction is not allowed."""

    BY_GROUP = "by_group"
    BY_TARGET = "by_target"
    ACTOR_NO_SEMEN = "actor_no_semen"
    TARGET_NO_SEMEN = "target_no_semen"


def check(
    kind: InteractionType,
    group_settings: GroupSettings,
    target_prefs: UserPreferences,
) -> Denial | None:
    """
    Returns None if the interaction is allowed, otherwise the denial reason.

    Precedence: group hard-ban > target personal opt-out. Group wins so admins
    can enforce a chat-wide rule regardless of individual preferences.
    """
    if kind not in group_settings.allowed_interactions:
        return Denial.BY_GROUP
    if not target_prefs.allows(kind):
        return Denial.BY_TARGET
    return None
