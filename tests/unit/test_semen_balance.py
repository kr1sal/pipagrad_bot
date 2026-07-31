from __future__ import annotations

from datetime import UTC, datetime, timedelta

from src.domain.entities.semen_balance import SemenBalance, SemenConfig
from src.domain.value_objects.telegram_ids import TelegramChatId

CFG = SemenConfig(base_cap_ml=20, cap_per_cm=2, regen_per_hour=6, fuck_cost_ml=20)


def _balance(stored: int, updated: datetime) -> SemenBalance:
    return SemenBalance(
        id=None,
        user_id=1,
        chat_id=TelegramChatId(100),
        stored_ml=stored,
        updated_at=updated,
    )


def test_cap_scales_linearly_with_size() -> None:
    assert CFG.cap_for(0) == 20
    assert CFG.cap_for(10) == 40
    assert CFG.cap_for(50) == 120
    assert CFG.cap_for(200) == 420


def test_cap_clamps_negative_size_to_zero() -> None:
    assert CFG.cap_for(-5) == 20


def test_initial_starts_at_supplied_cap() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    b = SemenBalance.initial(1, TelegramChatId(100), initial_ml=40, now=now)
    assert b.stored_ml == 40
    assert b.current_ml(now, CFG.regen_per_hour, cap_ml=40) == 40


def test_regen_capped_at_current_cap() -> None:
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    b = _balance(stored=10, updated=t0)
    # cap=40 (size=10): after 100h, gained=600, clamped to 40
    assert b.current_ml(t0 + timedelta(hours=100), CFG.regen_per_hour, cap_ml=40) == 40


def test_shrinking_cap_clamps_projected_value_down() -> None:
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    b = _balance(stored=80, updated=t0)
    # stored above new cap → current is clamped to new cap
    assert b.current_ml(t0, CFG.regen_per_hour, cap_ml=30) == 30


def test_try_spend_deducts_when_enough() -> None:
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    b = _balance(stored=50, updated=t0)
    new = b.try_spend(20, t0, CFG.regen_per_hour, cap_ml=100)
    assert new == 30
    assert b.stored_ml == 30
    assert b.updated_at == t0


def test_try_spend_returns_none_when_not_enough() -> None:
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    b = _balance(stored=5, updated=t0)
    assert b.try_spend(20, t0, CFG.regen_per_hour, cap_ml=100) is None
    assert b.stored_ml == 5


def test_try_spend_uses_projected_amount_and_respects_cap() -> None:
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    b = _balance(stored=0, updated=t0)
    later = t0 + timedelta(hours=5)  # +30 ml if unbounded, but clamped to cap
    new = b.try_spend(20, later, CFG.regen_per_hour, cap_ml=25)  # cap=25
    assert new == 5
    assert b.updated_at == later
