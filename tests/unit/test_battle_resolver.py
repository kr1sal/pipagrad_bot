from __future__ import annotations

import pytest

from src.domain.services.battle_resolver import resolve


@pytest.mark.parametrize(
    "c,o,roll,expected_challenger_wins",
    [
        (10, 5, 1, True),      # lowest roll -> challenger
        (10, 5, 10, True),     # boundary -> still challenger (roll <= size_c)
        (10, 5, 11, False),    # first opponent slot
        (10, 5, 15, False),    # top roll -> opponent
        (1, 9, 1, True),       # small chance still hits
        (1, 9, 2, False),      # everything else opponent
    ],
)
def test_proportional_chance_boundaries(
    c: int, o: int, roll: int, expected_challenger_wins: bool
) -> None:
    outcome = resolve(c, o, roll)
    assert outcome.challenger_wins is expected_challenger_wins


def test_both_zero_fifty_fifty() -> None:
    assert resolve(0, 0, 0).challenger_wins is True
    assert resolve(0, 0, 1).challenger_wins is False
