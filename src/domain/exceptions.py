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


class BattlesDisabled(DomainError):
    """Battles are turned off in this chat's settings."""


class BattleAlreadyActive(DomainError):
    """Challenger and opponent already have an unresolved battle between them."""


class InsufficientDickSize(DomainError):
    def __init__(self, needed: int, actual: int) -> None:
        super().__init__(f"Need {needed} cm, have {actual}")
        self.needed = needed
        self.actual = actual


class BattleNotFound(DomainError):
    pass


class BattleNotPending(DomainError):
    pass


class NotYourBattle(DomainError):
    """Someone other than the invited opponent tried to respond."""


class InsufficientPipaCoinBalance(DomainError):
    def __init__(self, needed: int, actual: int) -> None:
        super().__init__(f"Need {needed} PipaCoin, have {actual}")
        self.needed = needed
        self.actual = actual
