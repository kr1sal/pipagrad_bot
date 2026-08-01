from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.domain.entities.group import GroupSettings
from src.domain.value_objects.interaction_type import InteractionType


class SettingsCB(CallbackData, prefix="s"):
    """
    action:
      tb   - toggle battles
      tre  - toggle random events
      ti   - toggle interaction (needs kind)
    """

    action: str
    kind: str | None = None


def _flag(on: bool) -> str:
    return "✅" if on else "❌"


def build(settings: GroupSettings) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    kb.button(
        text=f"{_flag(settings.battles_enabled)} Битвы",
        callback_data=SettingsCB(action="tb").pack(),
    )
    kb.button(
        text=f"{_flag(settings.random_events_enabled)} Случайные события (12–24ч)",
        callback_data=SettingsCB(action="tre").pack(),
    )

    for kind, label in (
        (InteractionType.PET, "гладить"),
        (InteractionType.KISS, "целовать"),
        (InteractionType.FUCK, "трахать"),
    ):
        allowed = kind in settings.allowed_interactions
        kb.button(
            text=f"{_flag(allowed)} Разрешено {label}",
            callback_data=SettingsCB(action="ti", kind=kind.value).pack(),
        )

    kb.adjust(1)
    return kb.as_markup()


__all__ = ["SettingsCB", "build"]
