from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.domain.value_objects.pipacoin_transaction_kind import (
    PipaCoinTransactionKind,
)


@dataclass(frozen=True, slots=True)
class PipaCoinTransaction:
    """One immutable ledger entry against a user's PipaCoin wallet."""

    id: int | None
    user_id: int
    delta: int
    balance_after: int
    kind: PipaCoinTransactionKind
    counterparty_user_id: int | None
    created_at: datetime
