from __future__ import annotations

from datetime import timedelta
from html import escape

from src.domain.services.interaction_policy import Denial
from src.domain.value_objects.interaction_type import InteractionType

_VERB_PAST: dict[InteractionType, str] = {
    InteractionType.PET: "погладил",
    InteractionType.KISS: "поцеловал",
    InteractionType.FUCK: "трахнул",
}

_VERB_NOUN: dict[InteractionType, str] = {
    InteractionType.PET: "гладить",
    InteractionType.KISS: "целовать",
    InteractionType.FUCK: "трахать",
}


def mention(username: str | None, tg_id: int, display_name: str | None = None) -> str:
    label = display_name or (f"@{username}" if username else f"id{tg_id}")
    return f'<a href="tg://user?id={tg_id}">{escape(label)}</a>'


def start() -> str:
    return (
        "Добро пожаловать в <b>Pipagrad</b> 🍆\n\n"
        "Основные команды:\n"
        "• /grow — вырастить писюнчик (раз в сутки)\n"
        "• /pet | /kiss | /fuck — reply на сообщение\n"
        "• /me — что со мной можно делать в этом чате\n"
        "• /settings — настройки чата (только для админов)\n"
        "• /top — топ (скоро)\n"
    )


def grow_success(delta_cm: int, new_size_cm: int) -> str:
    if delta_cm > 0:
        line = f"Вырос на <b>+{delta_cm} см</b> 📈"
    elif delta_cm < 0:
        line = f"Уменьшился на <b>{delta_cm} см</b> 📉"
    else:
        line = "Размер не изменился 😐"
    return f"{line}\nТекущий размер: <b>{new_size_cm} см</b>"


def grow_cooldown(remaining: timedelta, current_size_cm: int) -> str:
    total = int(remaining.total_seconds())
    hours, rem = divmod(total, 3600)
    minutes = rem // 60
    return (
        f"⏳ Рано ещё! Приходи через <b>{hours}ч {minutes}м</b>.\n"
        f"Текущий размер: <b>{current_size_cm} см</b>"
    )


def settings_only_in_groups() -> str:
    return "Эта команда работает только в группе."


def settings_header() -> str:
    return (
        "<b>Настройки группы</b>\n"
        "Тумблеры влияют на всех участников. Меняют только админы."
    )


def settings_not_admin() -> str:
    return "🚫 Только админы группы могут менять настройки."


def interaction_needs_reply(kind: InteractionType) -> str:
    return f"Ответь на сообщение того, кого хочешь {_VERB_NOUN[kind]}."


def interaction_self() -> str:
    return "С собой — не в этом боте."


def interaction_done(
    kind: InteractionType,
    actor_mention: str,
    target_mention: str,
) -> str:
    verb = _VERB_PAST[kind]
    return f"{actor_mention} {verb} {target_mention} 💫"


def interaction_denied(kind: InteractionType, reason: Denial) -> str:
    verb = _VERB_NOUN[kind]
    if reason is Denial.BY_GROUP:
        return f"🚫 В этом чате запрещено {verb}."
    return f"🚫 Этот человек не разрешает {verb} себя."


def me_only_in_groups() -> str:
    return "Настройки взаимодействий работают в контексте группы. Позови меня в неё."


def me_header() -> str:
    return (
        "<b>Что со мной можно делать в этом чате</b>\n"
        "Если галочка стоит — разрешено. Настройки группы имеют приоритет."
    )
