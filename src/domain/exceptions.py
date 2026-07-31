from __future__ import annotations

from datetime import timedelta


class DomainError(Exception):
    """Base class for domain-layer errors."""


class CooldownActive(DomainError):
    def __init__(self, remaining: timedelta) -> None:
        super().__init__(f"Cooldown active, remaining={remaining}")
        self.remaining = remaining


class NotAnAdmin(DomainError):
    """Raised when a non-admin tries to change group-wide settings."""


class SelfInteraction(DomainError):
    """Raised when a user tries to interact with themselves."""
