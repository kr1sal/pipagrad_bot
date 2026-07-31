from __future__ import annotations

from datetime import UTC, datetime, timedelta

from src.domain.entities.semen_balance import SemenBalance, SemenConfig
from src.domain.value_objects.telegram_ids import TelegramChatId

CFG = SemenConfig(cap_ml=100, regen_per_hour=6, fuck_cost_ml=20)


def _balance(stored: int, updated: datetime) -> SemenBalance:
    return SemenBalance(
        id=None,
        user_id=1,
        chat_id=TelegramChatId(100),
        stored_ml=stored,
        updated_at=updated,
    )


def test_initial_starts_at_cap() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    b = SemenBalance.initial(1, TelegramChatId(100), CFG, now)
    assert b.stored_ml == CFG.cap_ml
    assert b.current_ml(now, CFG) == CFG.cap_ml


def test_regen_accumulates_up_to_cap() -> None:
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    b = _balance(stored=10, updated=t0)
    # after 5 hours: +30 ml -> 40
    assert b.current_ml(t0 + timedelta(hours=5), CFG) == 40
    # after 100 hours: clamped at cap
    assert b.current_ml(t0 + timedelta(hours=100), CFG) == 100


def test_try_spend_deducts_when_enough() -> None:
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    b = _balance(stored=50, updated=t0)
    new = b.try_spend(20, t0, CFG)
    assert new == 30
    assert b.stored_ml == 30
    assert b.updated_at == t0


def test_try_spend_returns_none_when_not_enough() -> None:
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    b = _balance(stored=5, updated=t0)
    assert b.try_spend(20, t0, CFG) is None
    # entity not mutated on failure
    assert b.stored_ml == 5


def test_try_spend_uses_projected_amount() -> None:
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    b = _balance(stored=0, updated=t0)
    later = t0 + timedelta(hours=5)  # +30 ml gained
    new = b.try_spend(20, later, CFG)
    assert new == 10
    assert b.updated_at == later
