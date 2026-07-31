from __future__ import annotations

from datetime import timedelta
from html import escape

from src.application.dto.stats import UserGlobalStats
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
        "• /battle [ставка] — вызов на битву (reply)\n"
        "• /top — топ 10 в этом чате\n"
        "• /me — что со мной можно делать в этом чате\n"
        "• /settings — настройки чата (только для админов)\n\n"
        "Ещё умею inline: набери <code>@pipagrad_bot</code> в любом чате."
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


def interaction_denied(
    kind: InteractionType,
    reason: Denial,
    current_ml: int | None = None,
    cost_ml: int | None = None,
) -> str:
    verb = _VERB_NOUN[kind]
    if reason is Denial.BY_GROUP:
        return f"🚫 В этом чате запрещено {verb}."
    if reason is Denial.BY_TARGET:
        return f"🚫 Этот человек не разрешает {verb} себя."
    if reason is Denial.ACTOR_NO_SEMEN:
        return (
            f"💤 У тебя не хватает спермы: <b>{current_ml}/{cost_ml} мл</b>.\n"
            f"Подожди, накопится — регенерация идёт со временем."
        )
    if reason is Denial.TARGET_NO_SEMEN:
        return (
            f"💤 У него/неё не хватает спермы: <b>{current_ml}/{cost_ml} мл</b>.\n"
            f"Не сегодня, увы."
        )
    return "🚫 Отказ."


def me_only_in_groups() -> str:
    return "Настройки взаимодействий работают в контексте группы. Позови меня в неё."


def me_header() -> str:
    return (
        "<b>Что со мной можно делать в этом чате</b>\n"
        "Если галочка стоит — разрешено. Настройки группы имеют приоритет."
    )


def battle_only_in_groups() -> str:
    return "Битвы — только в группах, вызывай reply на сообщение противника."


def battle_needs_reply() -> str:
    return "Ответь на сообщение того, с кем хочешь сразиться: /battle [ставка]."


def battle_bad_stake() -> str:
    return "Ставка — целое число ≥ 1 см."


def battles_disabled() -> str:
    return "🚫 Битвы отключены в этом чате."


def battle_challenge(
    challenger_mention: str, opponent_mention: str, stake_cm: int
) -> str:
    return (
        f"⚔️ {challenger_mention} вызывает {opponent_mention} на битву!\n"
        f"Ставка: <b>{stake_cm} см</b>. Ответ ждём 5 минут."
    )


def battle_insufficient(needed: int, actual: int) -> str:
    return f"Не хватает: нужно {needed} см, есть {actual}."


def battle_declined(opponent_mention: str) -> str:
    return f"✋ {opponent_mention} отклонил вызов."


def battle_expired() -> str:
    return "⏰ Вызов истёк."


def battle_not_your() -> str:
    return "Это не твой вызов — ответить может только вызванный."


def battle_not_pending() -> str:
    return "На этот вызов уже ответили."


def battle_resolved(
    winner_mention: str,
    loser_mention: str,
    stake_cm: int,
    winner_size_cm: int,
    loser_size_cm: int,
) -> str:
    return (
        f"🏆 Победил {winner_mention}!\n"
        f"{winner_mention}: <b>{winner_size_cm} см</b> (+{stake_cm})\n"
        f"{loser_mention}: <b>{loser_size_cm} см</b> (-{stake_cm})"
    )


def top_empty() -> str:
    return "Пока никто нигде не растил писюнчик. Напиши /grow в группе."


def top_header() -> str:
    return "<b>🏆 Глобальный топ</b> (по максимуму среди всех чатов)"


def top_line(rank: int, mention: str, size_cm: int) -> str:
    medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f" {rank}.")
    return f"{medal} {mention} — <b>{size_cm} см</b>"


def inline_card_title() -> str:
    return "🍆 Мой писюнчик"


def inline_card_description(stats: UserGlobalStats | None) -> str:
    if stats is None:
        return "Пока пусто — начни /grow в группе."
    return f"Максимум {stats.max_cm} см, всего {stats.total_cm} см в {stats.chats_count} чат(-ах)"


def inline_card_message(user_mention: str, stats: UserGlobalStats | None) -> str:
    if stats is None:
        return (
            f"У {user_mention} пока нет писюнчика 😢\n"
            f"Начни /grow в группе, чтобы им похвастаться."
        )
    return (
        f"🍆 <b>Писюнчик {user_mention}</b>\n"
        f"Максимум: <b>{stats.max_cm} см</b>\n"
        f"Всего: <b>{stats.total_cm} см</b> в {stats.chats_count} чат(-ах)"
    )
