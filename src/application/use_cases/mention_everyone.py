from __future__ import annotations

from src.application.ports.telegram_gateway import TelegramGateway
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.entities.user import User
from src.domain.exceptions import NotAnAdmin
from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId


class MentionEveryoneUseCase:
    """
    Lists everyone the bot has seen active in this chat (i.e. grown a dick
    here) — the Bot API gives no way to enumerate a group's full membership,
    so this is the best available stand-in for "everyone". Restricted to
    admins since it mass-pings the chat.
    """

    def __init__(self, uow: UnitOfWork, telegram: TelegramGateway) -> None:
        self._uow = uow
        self._telegram = telegram

    async def execute(
        self, chat_id: TelegramChatId, actor_tg_id: TelegramUserId
    ) -> list[User]:
        is_admin = await self._telegram.is_chat_admin(chat_id, actor_tg_id)
        if not is_admin:
            raise NotAnAdmin()

        async with self._uow as uow:
            dicks = await uow.dicks.list_for_chat(chat_id)
            users: list[User] = []
            for dick in dicks:
                user = await uow.users.get_by_id(dick.user_id)
                if user is not None:
                    users.append(user)
            return users
