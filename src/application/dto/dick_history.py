from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.domain.value_objects.dick_history_reason import DickHistoryReason


@dataclass(frozen=True, slots=True)
class DickHistoryLine:
    delta_cm: int
    new_size_cm: int
    reason: DickHistoryReason
    created_at: datetime


@dataclass(frozen=True, slots=True)
class DickHistoryPage:
    lines: list[DickHistoryLine]
    page: int
    has_prev: bool
    has_next: bool
