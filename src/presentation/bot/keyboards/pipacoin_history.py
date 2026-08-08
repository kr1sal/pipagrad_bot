from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class PipaHistoryCB(CallbackData, prefix="ph"):
    page: int


def build(page: int, has_prev: bool, has_next: bool) -> InlineKeyboardMarkup | None:
    if not has_prev and not has_next:
        return None
    kb = InlineKeyboardBuilder()
    if has_prev:
        kb.button(text="⬅️ Назад", callback_data=PipaHistoryCB(page=page - 1).pack())
    if has_next:
        kb.button(text="Вперёд ➡️", callback_data=PipaHistoryCB(page=page + 1).pack())
    kb.adjust(2)
    return kb.as_markup()


__all__ = ["PipaHistoryCB", "build"]
