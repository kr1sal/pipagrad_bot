from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.domain.value_objects.interaction_type import InteractionType
from src.domain.value_objects.user_preferences import UserPreferences


class PrefsCB(CallbackData, prefix="p"):
    kind: str


def _flag(on: bool) -> str:
    return "✅" if on else "❌"


def build(prefs: UserPreferences) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for kind, label in (
        (InteractionType.PET, "гладить"),
        (InteractionType.KISS, "целовать"),
        (InteractionType.FUCK, "трахать"),
    ):
        kb.button(
            text=f"{_flag(prefs.allows(kind))} Разрешаю {label} меня",
            callback_data=PrefsCB(kind=kind.value).pack(),
        )
    kb.adjust(1)
    return kb.as_markup()
