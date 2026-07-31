from __future__ import annotations

from datetime import timedelta


def start() -> str:
    return (
        "Привет! Я бот-писюнчик 🍆\n\n"
        "Основные команды:\n"
        "• /grow — вырастить писюнчик (раз в сутки)\n"
        "• /me — моя статистика (скоро)\n"
        "• /top — топ в этом чате (скоро)\n"
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
