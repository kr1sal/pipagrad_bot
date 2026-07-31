from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BattleOutcome:
    challenger_wins: bool


def resolve(
    challenger_size_cm: int,
    opponent_size_cm: int,
    roll: int,
) -> BattleOutcome:
    """
    Proportional-chance resolution: P(challenger wins) = size_c / (size_c + size_o).

    Pure function: caller provides `roll`, an integer in [1, size_c + size_o]
    (when total > 0) or in {0, 1} (when both sizes are 0, resolves 50/50).
    Keeping randomness out of domain lets tests be deterministic and keeps the
    dependency direction domain-independent.
    """
    total = challenger_size_cm + opponent_size_cm
    if total <= 0:
        return BattleOutcome(challenger_wins=roll == 0)
    return BattleOutcome(challenger_wins=roll <= challenger_size_cm)
