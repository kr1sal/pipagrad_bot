from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class BattleCB(CallbackData, prefix="b"):
    battle_id: int
    accept: bool


def build(battle_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="⚔️ Принять",
        callback_data=BattleCB(battle_id=battle_id, accept=True).pack(),
    )
    kb.button(
        text="✋ Отклонить",
        callback_data=BattleCB(battle_id=battle_id, accept=False).pack(),
    )
    kb.adjust(2)
    return kb.as_markup()
