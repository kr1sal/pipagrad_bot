from __future__ import annotations

from enum import Enum


class PipaCoinTransactionKind(str, Enum):
    EXCHANGE = "exchange"  # cm -> PipaCoin, minted into the wallet
    TRANSFER_SENT = "transfer_sent"
    TRANSFER_RECEIVED = "transfer_received"
