from __future__ import annotations

import logging

from aiogram import Router
from aiogram.types import (
    ChosenInlineResult,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    User,
)
from dishka.integrations.aiogram import FromDishka, inject

from src.application.dto.interaction import (
    InteractionDenied,
    PerformInteractionCommand,
)
from src.application.dto.stats import TopEntry, UserGlobalStats
from src.application.use_cases.find_user_by_username import (
    FindUserByUsernameUseCase,
    FoundUser,
)
from src.application.use_cases.get_global_top import GetGlobalTopUseCase
from src.application.use_cases.get_user_global_stats import GetUserGlobalStatsUseCase
from src.application.use_cases.perform_interaction import PerformInteractionUseCase
from src.domain.exceptions import SelfInteraction
from src.domain.value_objects.interaction_type import InteractionType
from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId
from src.presentation.bot.texts import ru as texts

log = logging.getLogger(__name__)

# Sentinel chat_id for user-to-user interactions triggered from inline mode.
# Real Telegram chat ids are never 0 (private > 0, groups < 0), so this can't
# clash with a live chat. All inline interactions share this one virtual chat,
# so semen/dick state accumulated via inline is separate from any real group.
DIRECT_CHAT_ID = TelegramChatId(0)

router = Router(name="inline")


@router.inline_query()
@inject
async def handle_inline(
    query: InlineQuery,
    get_stats: FromDishka[GetUserGlobalStatsUseCase],
    get_top: FromDishka[GetGlobalTopUseCase],
    find_user: FromDishka[FindUserByUsernameUseCase],
) -> None:
    actor = query.from_user
    text = (query.query or "").strip()

    # Query starts with a username → show action menu targeting that user.
    if text and _looks_like_username_query(text):
        username = text.lstrip("@").split()[0]
        target = await find_user.execute(username)
        results = _action_results(actor, target, username)
        await query.answer(results=results, cache_time=5, is_personal=True)
        return

    # Otherwise the default menu: my card, top, help.
    stats = await get_stats.execute(TelegramUserId(actor.id))
    top = await get_top.execute(limit=10)
    mention = texts.mention(actor.username, actor.id, actor.full_name)
    results = [
        _card_result(actor.id, mention, stats),
        _top_result(top),
        _help_result(),
    ]
    await query.answer(results=results, cache_time=30, is_personal=True)


def _looks_like_username_query(text: str) -> bool:
    """
    Treat anything starting with '@' as a username query, and also plain words
    that look username-shaped (letters/digits/underscore, 5+ chars, no spaces).
    Telegram requires usernames to be at least 5 chars — enforcing that here
    avoids showing action menus for anything the user types accidentally.
    """
    first = text.split()[0]
    if first.startswith("@"):
        return True
    return len(first) >= 5 and all(
        c.isalnum() or c == "_" for c in first
    )


def _action_results(
    actor: User, target: FoundUser | None, requested_username: str
) -> list[InlineQueryResultArticle]:
    if target is None:
        return [
            InlineQueryResultArticle(
                id=f"nouser-{requested_username}",
                title=texts.inline_no_such_user_title(requested_username),
                description=texts.inline_no_such_user_description(),
                input_message_content=InputTextMessageContent(
                    message_text=texts.inline_no_such_user_message(
                        requested_username
                    ),
                    parse_mode="HTML",
                ),
            )
        ]

    actor_mention = texts.mention(actor.username, actor.id, actor.full_name)
    target_mention = texts.mention(target.username, int(target.tg_id), None)
    return [
        _action_result(
            kind=kind,
            actor=actor,
            target=target,
            actor_mention=actor_mention,
            target_mention=target_mention,
        )
        for kind in (
            InteractionType.PET,
            InteractionType.KISS,
            InteractionType.HUG,
            InteractionType.FUCK,
        )
    ]


def _action_result(
    *,
    kind: InteractionType,
    actor: User,
    target: FoundUser,
    actor_mention: str,
    target_mention: str,
) -> InlineQueryResultArticle:
    return InlineQueryResultArticle(
        id=f"{kind.value}-{actor.id}-{int(target.tg_id)}",
        title=texts.inline_action_title(kind, target.username),
        description=texts.inline_action_description(kind),
        input_message_content=InputTextMessageContent(
            message_text=texts.inline_action_message(
                kind, actor_mention, target_mention
            ),
            parse_mode="HTML",
        ),
    )


def _card_result(
    user_tg_id: int, mention: str, stats: UserGlobalStats | None
) -> InlineQueryResultArticle:
    return InlineQueryResultArticle(
        id=f"card-{user_tg_id}",
        title=texts.inline_card_title(),
        description=texts.inline_card_description(stats),
        input_message_content=InputTextMessageContent(
            message_text=texts.inline_card_message(mention, stats),
            parse_mode="HTML",
        ),
    )


def _top_result(top: list[TopEntry]) -> InlineQueryResultArticle:
    return InlineQueryResultArticle(
        id="top",
        title=texts.inline_top_title(),
        description=texts.inline_top_description(top),
        input_message_content=InputTextMessageContent(
            message_text=texts.inline_top_message(top),
            parse_mode="HTML",
        ),
    )


def _help_result() -> InlineQueryResultArticle:
    return InlineQueryResultArticle(
        id="help",
        title=texts.inline_help_title(),
        description=texts.inline_help_description(),
        input_message_content=InputTextMessageContent(
            message_text=texts.inline_help_message(),
            parse_mode="HTML",
        ),
    )


# ---------------------------------------------------------------- mutation

# Result ids for action articles: "{kind}-{actor_id}-{target_tg_id}".
# Non-action results (card / top / help) don't match this shape and are ignored.
_ACTION_KINDS = {k.value for k in InteractionType}


@router.chosen_inline_result()
@inject
async def on_chosen_action(
    chosen: ChosenInlineResult,
    perform: FromDishka[PerformInteractionUseCase],
) -> None:
    """
    Fires when the user actually picks an inline article — this is our only
    signal that an action happened, because the message that gets posted has
    no chat_id and no callback (there was no accept flow to hook into).
    Applies the interaction against a sentinel chat so semen is actually
    spent, even though the visible message was already sent.

    Requires @BotFather → /setinlinefeedback → Enabled, otherwise Telegram
    doesn't dispatch this update.
    """
    parsed = _parse_action_id(chosen.result_id)
    if parsed is None:
        return  # a non-action article (card / top / help) — nothing to apply
    kind, actor_tg_id, target_tg_id = parsed
    if int(chosen.from_user.id) != actor_tg_id:
        # someone forged/replayed a result_id — ignore
        return

    try:
        result = await perform.execute(
            PerformInteractionCommand(
                chat_id=DIRECT_CHAT_ID,
                actor_tg_id=TelegramUserId(actor_tg_id),
                actor_username=chosen.from_user.username,
                target_tg_id=TelegramUserId(target_tg_id),
                target_username=None,  # target isn't in this event; already saved
                kind=kind,
            )
        )
    except SelfInteraction:
        return

    if isinstance(result, InteractionDenied):
        # Message already went out; without an inline_message_id (no reply_markup
        # on the article) we can't edit it, so denial is best-effort logged.
        log.info(
            "inline action denied: kind=%s actor=%s target=%s reason=%s "
            "current_ml=%s cost_ml=%s",
            kind.value, actor_tg_id, target_tg_id, result.reason.value,
            result.current_ml, result.cost_ml,
        )


def _parse_action_id(
    result_id: str,
) -> tuple[InteractionType, int, int] | None:
    parts = result_id.split("-")
    if len(parts) != 3:
        return None
    kind_str, actor_str, target_str = parts
    if kind_str not in _ACTION_KINDS:
        return None
    try:
        actor_id = int(actor_str)
        target_id = int(target_str)
    except ValueError:
        return None
    return InteractionType(kind_str), actor_id, target_id
