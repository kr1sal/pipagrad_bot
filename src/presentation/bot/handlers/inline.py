from __future__ import annotations

from aiogram import Router
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from dishka.integrations.aiogram import FromDishka, inject

from src.application.use_cases.get_user_global_stats import GetUserGlobalStatsUseCase
from src.domain.value_objects.telegram_ids import TelegramUserId
from src.presentation.bot.texts import ru as texts

router = Router(name="inline")


@router.inline_query()
@inject
async def handle_inline(
    query: InlineQuery,
    get_stats: FromDishka[GetUserGlobalStatsUseCase],
) -> None:
    user = query.from_user
    stats = await get_stats.execute(TelegramUserId(user.id))
    mention = texts.mention(user.username, user.id, user.full_name)

    article = InlineQueryResultArticle(
        id=f"card-{user.id}",
        title=texts.inline_card_title(),
        description=texts.inline_card_description(stats),
        input_message_content=InputTextMessageContent(
            message_text=texts.inline_card_message(mention, stats),
            parse_mode="HTML",
        ),
    )
    # short cache so numbers update within a minute after /grow
    await query.answer(results=[article], cache_time=30, is_personal=True)
