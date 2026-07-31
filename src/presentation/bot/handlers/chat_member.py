from __future__ import annotations

from aiogram import Router
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.types import ChatMemberUpdated
from dishka.integrations.aiogram import FromDishka, inject

from src.application.dto.group_settings import EnsureGroupRegisteredCommand
from src.application.use_cases.ensure_group_registered import (
    EnsureGroupRegisteredUseCase,
)
from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId

router = Router(name="chat_member")

_GROUP_TYPES = {ChatType.GROUP, ChatType.SUPERGROUP}
_JOINED_STATUSES = {
    ChatMemberStatus.MEMBER,
    ChatMemberStatus.ADMINISTRATOR,
}


@router.my_chat_member()
@inject
async def on_my_chat_member(
    event: ChatMemberUpdated,
    ensure_group: FromDishka[EnsureGroupRegisteredUseCase],
) -> None:
    if event.chat.type not in _GROUP_TYPES:
        return
    if event.new_chat_member.status not in _JOINED_STATUSES:
        return
    await ensure_group.execute(
        EnsureGroupRegisteredCommand(
            chat_id=TelegramChatId(event.chat.id),
            title=event.chat.title,
            added_by_tg_id=(
                TelegramUserId(event.from_user.id) if event.from_user else None
            ),
        )
    )
