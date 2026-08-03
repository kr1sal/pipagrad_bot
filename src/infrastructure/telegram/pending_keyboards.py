from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class OrgyCB(CallbackData, prefix="og"):
    event_id: int


class BotBattleCB(CallbackData, prefix="bb"):
    event_id: int
    side: str  # "pipa" or "other"


class TeamBattleCB(CallbackData, prefix="tb"):
    event_id: int
    side: int  # 1 (challenger's side) or 2 (opponent's side)


def orgy_keyboard(event_id: int, joined_count: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text=f"🎉 Присоединиться ({joined_count})",
        callback_data=OrgyCB(event_id=event_id).pack(),
    )
    kb.adjust(1)
    return kb.as_markup()


def bot_battle_keyboard(
    event_id: int, pipa_count: int, other_count: int, other_label: str
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text=f"⚔️ За Pipagrad ({pipa_count})",
        callback_data=BotBattleCB(event_id=event_id, side="pipa").pack(),
    )
    kb.button(
        text=f"🤖 За {other_label} ({other_count})",
        callback_data=BotBattleCB(event_id=event_id, side="other").pack(),
    )
    kb.adjust(2)
    return kb.as_markup()


def team_battle_keyboard(
    event_id: int,
    side1_count: int,
    side2_count: int,
    challenger_label: str,
    opponent_label: str,
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text=f"⚔️ {challenger_label} ({side1_count})",
        callback_data=TeamBattleCB(event_id=event_id, side=1).pack(),
    )
    kb.button(
        text=f"⚔️ {opponent_label} ({side2_count})",
        callback_data=TeamBattleCB(event_id=event_id, side=2).pack(),
    )
    kb.adjust(2)
    return kb.as_markup()
