from __future__ import annotations

from aiogram import Router
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from dishka.integrations.aiogram import FromDishka, inject

from src.application.dto.stats import TopEntry, UserGlobalStats
from src.application.use_cases.get_global_top import GetGlobalTopUseCase
from src.application.use_cases.get_user_global_stats import GetUserGlobalStatsUseCase
from src.domain.value_objects.telegram_ids import TelegramUserId
from src.presentation.bot.texts import ru as texts

router = Router(name="inline")


@router.inline_query()
@inject
async def handle_inline(
    query: InlineQuery,
    get_stats: FromDishka[GetUserGlobalStatsUseCase],
    get_top: FromDishka[GetGlobalTopUseCase],
) -> None:
    user = query.from_user
    stats = await get_stats.execute(TelegramUserId(user.id))
    top = await get_top.execute(limit=10)
    mention = texts.mention(user.username, user.id, user.full_name)

    results = [
        _card_result(user.id, mention, stats),
        _top_result(top),
        _help_result(),
    ]

    # short cache so numbers update within a minute after /grow;
    # is_personal=True keeps each user's results private (their card is theirs)
    await query.answer(
        results=results,
        cache_time=30,
        is_personal=True,
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
