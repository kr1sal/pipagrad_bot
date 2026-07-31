from __future__ import annotations

from dataclasses import dataclass, replace

from src.domain.value_objects.interaction_type import InteractionType


@dataclass(frozen=True, slots=True)
class UserPreferences:
    """
    What a user allows others to do to them, scoped per chat.
    Defaults are permissive — a user opts out, not in.
    """

    allowed: frozenset[InteractionType]

    @classmethod
    def default(cls) -> UserPreferences:
        return cls(allowed=frozenset(InteractionType))

    def toggled(self, kind: InteractionType) -> UserPreferences:
        allowed = set(self.allowed)
        if kind in allowed:
            allowed.remove(kind)
        else:
            allowed.add(kind)
        return replace(self, allowed=frozenset(allowed))

    def allows(self, kind: InteractionType) -> bool:
        return kind in self.allowed
