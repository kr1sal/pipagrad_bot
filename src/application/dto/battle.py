from __future__ import annotations

from dataclasses import dataclass

from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId


@dataclass(frozen=True, slots=True)
class ChallengeBattleCommand:
    chat_id: TelegramChatId
    challenger_tg_id: TelegramUserId
    challenger_username: str | None
    opponent_tg_id: TelegramUserId
    opponent_username: str | None
    stake_cm: int


@dataclass(frozen=True, slots=True)
class BattleChallenged:
    battle_id: int
    stake_cm: int


@dataclass(frozen=True, slots=True)
class RespondToBattleCommand:
    battle_id: int
    actor_tg_id: TelegramUserId
    accept: bool


@dataclass(frozen=True, slots=True)
class BattleResolvedResult:
    stake_cm: int
    winner_tg_id: TelegramUserId
    loser_tg_id: TelegramUserId
    winner_new_size_cm: int
    loser_new_size_cm: int


@dataclass(frozen=True, slots=True)
class BattleDeclinedResult:
    challenger_tg_id: TelegramUserId
    opponent_tg_id: TelegramUserId


@dataclass(frozen=True, slots=True)
class BattleExpiredResult:
    pass
