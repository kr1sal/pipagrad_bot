from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.domain.entities.group import ALLOWED_RANDOM_EVENT_INTERVALS_MIN, GroupSettings
from src.domain.value_objects.interaction_type import InteractionType


class SettingsCB(CallbackData, prefix="s"):
    """
    action:
      tb   - toggle battles
      tre  - toggle random events
      ti   - toggle interaction (needs kind)
      sri  - set random event interval (needs value)
    """

    action: str
    kind: str | None = None
    value: int | None = None


def _flag(on: bool) -> str:
    return "✅" if on else "❌"


def build(settings: GroupSettings) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    kb.button(
        text=f"{_flag(settings.battles_enabled)} Битвы",
        callback_data=SettingsCB(action="tb").pack(),
    )
    kb.button(
        text=f"{_flag(settings.random_events_enabled)} Случайные события",
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

    for m in ALLOWED_RANDOM_EVENT_INTERVALS_MIN:
        selected = "🔘" if m == settings.random_event_interval_minutes else "⚪"
        kb.button(
            text=f"{selected} {m}м",
            callback_data=SettingsCB(action="sri", value=m).pack(),
        )

    # layout: 1 per row for toggles, 5 for intervals
    kb.adjust(1, 1, 1, 1, 1, len(ALLOWED_RANDOM_EVENT_INTERVALS_MIN))
    return kb.as_markup()


__all__ = ["SettingsCB", "build"]


# small helper re-exports
def button(text: str, cb: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=cb)
