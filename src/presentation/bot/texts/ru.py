from __future__ import annotations

from datetime import timedelta
from html import escape

from src.application.dto.stats import MyChatBalance, TopEntry, UserGlobalStats
from src.domain.services.interaction_policy import Denial
from src.domain.value_objects.interaction_type import InteractionType

_VERB_PAST: dict[InteractionType, str] = {
    InteractionType.PET: "погладил",
    InteractionType.KISS: "поцеловал",
    InteractionType.FUCK: "трахнул",
    InteractionType.HUG: "обнял",
}

_VERB_NOUN: dict[InteractionType, str] = {
    InteractionType.PET: "гладить",
    InteractionType.KISS: "целовать",
    InteractionType.FUCK: "трахать",
    InteractionType.HUG: "обнимать",
}


def mention(username: str | None, tg_id: int, display_name: str | None = None) -> str:
    label = display_name or (f"@{username}" if username else f"id{tg_id}")
    return f'<a href="tg://user?id={tg_id}">{escape(label)}</a>'


def start() -> str:
    return (
        "Добро пожаловать в <b>Pipagrad</b> 🍆\n\n"
        "Основные команды:\n"
        "• /grow — вырастить писюнчик (раз в сутки)\n"
        "• /pet | /kiss | /hug | /fuck — reply <b>или</b> <code>@username</code>\n"
        "• /battle [ставка] — вызов на битву (reply)\n"
        "• /top — глобальный топ\n"
        "• /me — мой профиль в этом чате\n"
        "• /settings — настройки чата (только админы)\n\n"
        "Ещё умею inline: набери <code>@pipagrad_bot</code> в любом чате "
        "или <code>@pipagrad_bot @username</code> чтобы взаимодействовать."
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


def interaction_needs_target(kind: InteractionType) -> str:
    verb = _VERB_NOUN[kind]
    return (
        f"Кого {verb}? Либо ответь на его сообщение, либо укажи "
        f"<code>/{kind.value} @username</code>."
    )


def interaction_user_not_found(username: str) -> str:
    return (
        f"Не знаю @{username} — он должен хотя бы раз нажать /start "
        f"у @pipagrad_bot."
    )


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


def gift_needs_target() -> str:
    return (
        "Кому дарить? <code>/gift см</code> в ответ на сообщение, либо "
        "<code>/gift см @username</code>."
    )


def gift_bad_amount() -> str:
    return "Укажи сколько см дарить, например <code>/gift 5 @username</code>."


def gift_self() -> str:
    return "Самому себе — так себе подарок."


def gift_insufficient(needed: int, actual: int) -> str:
    return (
        f"🚫 Не хватает см на подарок: нужно <b>{needed} см</b>, "
        f"есть <b>{actual} см</b>."
    )


def gift_done(
    actor_mention: str,
    target_mention: str,
    amount_cm: int,
    actor_new_size_cm: int,
    target_new_size_cm: int,
) -> str:
    return (
        f"🎁 {actor_mention} подарил {amount_cm} см писюнчика {target_mention}\n"
        f"Теперь у {actor_mention} <b>{actor_new_size_cm} см</b>, "
        f"у {target_mention} <b>{target_new_size_cm} см</b>."
    )


def me_only_in_groups() -> str:
    return "Настройки взаимодействий работают в контексте группы. Позови меня в неё."


def me_header(balance: MyChatBalance) -> str:
    return (
        "<b>Мой профиль в этом чате</b>\n"
        f"🍆 Писюнчик: <b>{balance.dick_size_cm} см</b>\n"
        f"💦 Сперма: <b>{balance.semen_current_ml}/{balance.semen_cap_ml} мл</b> "
        f"(+{balance.regen_per_hour} мл/час)\n\n"
        "<b>Что со мной можно делать</b>\n"
        "Тумблеры ниже — разрешения для других. Настройки группы имеют приоритет."
    )


def battle_only_in_groups() -> str:
    return "Битвы — только в группах, вызывай reply на сообщение противника."


def battle_needs_reply() -> str:
    return "Ответь на сообщение того, с кем хочешь сразиться: /battle [ставка]."


def battle_bad_stake() -> str:
    return "Ставка — целое число ≥ 1 см."


def battles_disabled() -> str:
    return "🚫 Битвы отключены в этом чате."


def battle_already_active() -> str:
    return "⚔️ У вас уже есть незавершённая битва друг с другом — доиграйте её."


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


def battle_opened(
    challenger_mention: str, opponent_mention: str, stake_cm: int, minutes: int
) -> str:
    return (
        f"⚔️ Битва началась: {challenger_mention} vs {opponent_mention}!\n"
        f"Ставка <b>{stake_cm} см</b> достанется победившему из них двоих.\n"
        f"Присоединяйтесь к любой стороне ({minutes} мин) — вы не рискуете "
        f"своими см, но шанс победы вашей стороны зависит от числа игроков, "
        f"а не от размера."
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


def inline_top_title() -> str:
    return "🏆 Глобальный топ 10"


def inline_top_description(top: list[TopEntry]) -> str:
    if not top:
        return "Пока пусто — никто не растил."
    leader = top[0]
    label = leader.username or f"id{leader.tg_id}"
    return f"Лидер: @{label} — {leader.size_cm} см"


def inline_top_message(top: list[TopEntry]) -> str:
    if not top:
        return top_empty()
    lines = [top_header()]
    for e in top:
        lines.append(
            top_line(rank=e.rank, mention=mention(e.username, int(e.tg_id)), size_cm=e.size_cm)
        )
    return "\n".join(lines)


def inline_help_title() -> str:
    return "ℹ️ Как играть"


def inline_help_description() -> str:
    return "Список команд и что они делают"


def orgy_toast_joined() -> str:
    return "Ты в деле."


def orgy_toast_left() -> str:
    return "Ты передумал(-а)."


def bot_battle_toast_side(side_label: str) -> str:
    return f"Ты за {side_label}."


def bot_battle_not_your_side() -> str:
    return "Одна сторона на игрока — выбор нельзя менять."


def pending_not_found() -> str:
    return "Это событие уже завершилось."


def inline_action_title(kind: InteractionType, target_username: str) -> str:
    verb_map = {
        InteractionType.PET: "🥰 Погладить",
        InteractionType.KISS: "💋 Поцеловать",
        InteractionType.HUG: "🤗 Обнять",
        InteractionType.FUCK: "🍆 Трахнуть",
    }
    return f"{verb_map[kind]} @{target_username}"


def inline_action_description(kind: InteractionType) -> str:
    return {
        InteractionType.PET: "Отправить в чат «погладил»",
        InteractionType.KISS: "Отправить в чат «поцеловал»",
        InteractionType.HUG: "Отправить в чат «обнял»",
        InteractionType.FUCK: "Отправить в чат «трахнул»",
    }[kind]


def inline_action_message(
    kind: InteractionType, actor_mention: str, target_mention: str
) -> str:
    return f"{actor_mention} {_VERB_PAST[kind]} {target_mention} 💫"


def inline_no_such_user_title(username: str) -> str:
    return f"❌ @{username} ещё не играет"


def inline_no_such_user_description() -> str:
    return "Он должен хотя бы раз нажать /start у бота."


def inline_no_such_user_message(username: str) -> str:
    return (
        f"Я не знаю @{username} — попроси его нажать /start "
        f"в @pipagrad_bot, и он появится."
    )


def inline_help_message() -> str:
    return (
        "<b>Pipagrad</b> — как играть 🍆\n\n"
        "• /grow — вырастить писюнчик (раз в сутки)\n"
        "• /pet | /kiss | /fuck — reply на сообщение\n"
        "• /battle [ставка] — вызов на битву (reply)\n"
        "• /top — глобальный топ\n"
        "• /me — мой профиль в этом чате\n"
        "• /settings — настройки чата (только админы)\n\n"
        "Сперма копится со временем и тратится при /fuck. "
        "Максимум растёт вместе с размером писюнчика."
    )
