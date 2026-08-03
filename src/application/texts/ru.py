from __future__ import annotations

# ---------------------------------------------------------------- immediate

def meteor(loss: int, new_size_cm: int) -> str:
    return (
        f"☄️ <b>Метеорит</b> упал в чат и попал по одному из вас!\n"
        f"−{loss} см — новый размер: <b>{new_size_cm} см</b>"
    )


def radiation(gained: int, lost: int) -> str:
    return (
        f"☢️ <b>Радиация</b> прошла по чату. "
        f"Выросли: {gained}, уменьшились: {lost}."
    )


def spontaneous_battle(
    winner_ref: str, loser_ref: str, stake: int, winner_cm: int, loser_cm: int
) -> str:
    return (
        f"⚔️ <b>Внезапная битва!</b>\n"
        f"{winner_ref} побеждает {loser_ref} и забирает {stake} см.\n"
        f"Победитель: <b>{winner_cm} см</b> / "
        f"Проигравший: <b>{loser_cm} см</b>"
    )


def hurricane(victims_count: int, total_loss: int) -> str:
    return (
        f"🌪 <b>Ураган</b> сметает половину чата!\n"
        f"Пострадало: {victims_count} игрок(-ов), суммарно −{total_loss} см."
    )


def gift(ref: str, bonus: int, new_size_cm: int) -> str:
    return (
        f"🎁 <b>Подарок с небес!</b>\n"
        f"{ref} получает <b>+{bonus} см</b>. Новый размер: "
        f"<b>{new_size_cm} см</b>."
    )


def viagra(players_count: int) -> str:
    return (
        f"💊 <b>Виагра!</b>\n"
        f"У всех {players_count} игрок(-ов) сперма мгновенно до максимума."
    )


def ice_age_no_effect() -> str:
    return "🥶 <b>Заморозка</b> прошла впустую — никто не был на кулдауне."


def ice_age(reset_count: int) -> str:
    return (
        f"🥶 <b>Ледниковый период!</b>\n"
        f"Cooldown /grow сброшен у <b>{reset_count}</b> игрок(-ов) — можно снова расти."
    )


def royal_battle(
    champ_ref: str, champion_cm: int, fin_ref: str, finalist_cm: int
) -> str:
    return (
        f"👑 <b>Королевская битва!</b>\n"
        f"🥇 {champ_ref} — <b>+9 см</b>, теперь <b>{champion_cm} см</b>\n"
        f"🥈 {fin_ref} — <b>+3 см</b>, теперь <b>{finalist_cm} см</b>\n"
        f"Полуфиналисты выбывают с −3 см."
    )


# -------------------------------------------------------------------- orgy

def orgy_announcement(minutes_left: int) -> str:
    return (
        f"🎉 <b>Групповой секс!</b>\n"
        f"Кто хочет — жми кнопку. Старт через <b>{minutes_left} мин</b>.\n"
        f"Каждый участник потратит 10 мл спермы; кому хватит — получит +2 см."
    )


def orgy_resolved_nobody(participants_count: int) -> str:
    return (
        f"🎉 <b>Групповой секс закончен.</b>\n"
        f"Собралось {participants_count}, но ни у кого не хватило "
        f"спермы. Позор."
    )


def orgy_resolved(participants_count: int, succeeded: int, bonus: int) -> str:
    return (
        f"🎉 <b>Групповой секс закончен!</b>\n"
        f"Пришло: {participants_count}, отыгрались: "
        f"<b>{succeeded}</b>.\n"
        f"Каждому +{bonus} см."
    )


# ------------------------------------------------------------- bot battle

def bot_battle_announcement(minutes_left: int, other_label: str) -> str:
    return (
        f"🤖 <b>Битва ботов!</b>\n"
        f"<b>Pipagrad</b> vs <b>{other_label}</b>.\n"
        f"Выбирай сторону — базовые силы 100/100, каждый игрок добавляет "
        f"своим размером к своей стороне.\n"
        f"Итог через <b>{minutes_left} мин</b>. Если Pipagrad побеждает — "
        f"{other_label} вылетает из чата."
    )


def bot_battle_resolved_pipa_won(
    other_label: str, pipa_pot: int, other_pot: int
) -> str:
    return (
        f"🏆 <b>Pipagrad побеждает!</b> "
        f"({pipa_pot} против {other_pot})\n"
        f"{other_label} будет изгнан из чата."
    )


def bot_battle_resolved_other_won(
    other_label: str, pipa_pot: int, other_pot: int
) -> str:
    return (
        f"💀 <b>{other_label} побеждает.</b> "
        f"({other_pot} против {pipa_pot})\n"
        f"Pipagrad сохраняет достоинство и уходит зализывать раны."
    )


# ------------------------------------------------------------ team battle

def team_battle_resolved(
    winner_label: str,
    loser_label: str,
    stake_cm: int,
    winner_size_cm: int,
    loser_size_cm: int,
    winner_count: int,
    loser_count: int,
) -> str:
    return (
        f"🏆 <b>Сторона {winner_label}</b> побеждает! "
        f"({winner_count} против {loser_count} игроков)\n"
        f"{winner_label}: <b>{winner_size_cm} см</b> (+{stake_cm})\n"
        f"{loser_label}: <b>{loser_size_cm} см</b> (-{stake_cm})"
    )
