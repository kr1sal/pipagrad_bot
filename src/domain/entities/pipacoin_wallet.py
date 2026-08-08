from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.domain.exceptions import InsufficientPipaCoinBalance


@dataclass(slots=True)
class PipaCoinWallet:
    """
    A user's global PipaCoin balance — one wallet per user, shared across every
    chat (unlike dick size / semen, which are chat-scoped). Mirrors a bank
    account: `balance` is a materialized cache, kept consistent with the
    immutable PipaCoinTransaction ledger by always mutating both in the same
    transaction.
    """

    id: int | None
    user_id: int
    balance: int
    updated_at: datetime

    @classmethod
    def initial(cls, user_id: int, now: datetime) -> PipaCoinWallet:
        return cls(id=None, user_id=user_id, balance=0, updated_at=now)

    def credit(self, amount: int, now: datetime) -> None:
        if amount <= 0:
            raise ValueError("amount must be positive")
        self.balance += amount
        self.updated_at = now

    def debit(self, amount: int, now: datetime) -> None:
        if amount <= 0:
            raise ValueError("amount must be positive")
        if amount > self.balance:
            raise InsufficientPipaCoinBalance(needed=amount, actual=self.balance)
        self.balance -= amount
        self.updated_at = now
