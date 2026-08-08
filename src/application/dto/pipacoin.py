from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.domain.value_objects.pipacoin_transaction_kind import (
    PipaCoinTransactionKind,
)
from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId


@dataclass(frozen=True, slots=True)
class ExchangeSizeCommand:
    tg_user_id: TelegramUserId
    tg_username: str | None
    chat_id: TelegramChatId
    amount_cm: int


@dataclass(frozen=True, slots=True)
class ExchangeSizeResult:
    spent_cm: int
    gained_pipacoin: int
    new_size_cm: int
    new_balance: int


@dataclass(frozen=True, slots=True)
class TransferPipaCoinCommand:
    actor_tg_id: TelegramUserId
    actor_username: str | None
    target_tg_id: TelegramUserId
    target_username: str | None
    amount: int


@dataclass(frozen=True, slots=True)
class TransferPipaCoinResult:
    amount: int
    actor_new_balance: int
    target_new_balance: int


@dataclass(frozen=True, slots=True)
class PipaCoinHistoryLine:
    delta: int
    balance_after: int
    kind: PipaCoinTransactionKind
    counterparty_label: str | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class PipaCoinHistoryPage:
    lines: list[PipaCoinHistoryLine]
    page: int
    has_prev: bool
    has_next: bool
