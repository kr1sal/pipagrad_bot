from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from src.domain.entities.dick import Dick
from src.domain.exceptions import CooldownActive
from src.domain.value_objects.telegram_ids import TelegramChatId


def _dick() -> Dick:
    return Dick.initial(user_id=1, chat_id=TelegramChatId(100))


def test_initial_size_is_zero() -> None:
    d = _dick()
    assert d.size.cm == 0
    assert d.last_grow_at is None


def test_grow_applies_delta_and_sets_timestamp() -> None:
    d = _dick()
    now = datetime(2026, 1, 1, tzinfo=UTC)
    applied = d.grow(7, now, timedelta(hours=24))
    assert applied == 7
    assert d.size.cm == 7
    assert d.last_grow_at == now


def test_grow_clamped_at_zero() -> None:
    d = _dick()
    now = datetime(2026, 1, 1, tzinfo=UTC)
    applied = d.grow(-5, now, timedelta(hours=24))
    assert applied == 0
    assert d.size.cm == 0


def test_grow_raises_when_cooldown_active() -> None:
    d = _dick()
    now = datetime(2026, 1, 1, tzinfo=UTC)
    d.grow(5, now, timedelta(hours=24))
    with pytest.raises(CooldownActive):
        d.grow(5, now + timedelta(hours=1), timedelta(hours=24))


def test_grow_allowed_after_cooldown() -> None:
    d = _dick()
    now = datetime(2026, 1, 1, tzinfo=UTC)
    d.grow(5, now, timedelta(hours=24))
    d.grow(3, now + timedelta(hours=24), timedelta(hours=24))
    assert d.size.cm == 8
