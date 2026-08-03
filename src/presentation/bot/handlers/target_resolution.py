from __future__ import annotations

from dataclasses import dataclass

from aiogram.types import Message

from src.application.use_cases.find_user_by_username import FindUserByUsernameUseCase


@dataclass(frozen=True, slots=True)
class ResolvedTarget:
    tg_id: int
    username: str | None
    display_name: str | None  # only known when we resolved via a live reply


async def resolve_target(
    message: Message,
    raw_username: str | None,
    find_user: FindUserByUsernameUseCase,
) -> ResolvedTarget | None:
    """
    Two ways to name a target: reply to their message, or an explicit
    `@username` token. Reply wins when both are given — the id it carries is
    authoritative, while a looked-up username only reflects the last one we
    saw for that Telegram id.

    `tg_id=0` is a sentinel: an `@username` was given but isn't a user we
    know (they must interact with the bot at least once first).
    """
    replied = message.reply_to_message
    if replied and replied.from_user and not replied.from_user.is_bot:
        u = replied.from_user
        return ResolvedTarget(tg_id=u.id, username=u.username, display_name=u.full_name)

    if raw_username:
        username = raw_username.lstrip("@")
        if username:
            found = await find_user.execute(username)
            if found is not None:
                return ResolvedTarget(
                    tg_id=int(found.tg_id), username=found.username, display_name=None
                )
            return ResolvedTarget(tg_id=0, username=username, display_name=None)

    return None
