from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.group import Group, GroupSettings
from src.domain.value_objects.interaction_type import InteractionType
from src.domain.value_objects.telegram_ids import TelegramChatId, TelegramUserId
from src.infrastructure.persistence.models import GroupModel


class SqlAlchemyGroupRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, chat_id: TelegramChatId) -> Group | None:
        stmt = select(GroupModel).where(GroupModel.chat_id == int(chat_id))
        row = await self._session.scalar(stmt)
        return _to_entity(row) if row else None

    async def add(self, group: Group) -> Group:
        model = GroupModel(
            chat_id=int(group.chat_id),
            title=group.title,
            added_by_tg_id=int(group.added_by_tg_id) if group.added_by_tg_id else None,
            created_at=group.created_at,
            battles_enabled=group.settings.battles_enabled,
            random_events_enabled=group.settings.random_events_enabled,
            random_event_interval_minutes=group.settings.random_event_interval_minutes,
            allow_pet=InteractionType.PET in group.settings.allowed_interactions,
            allow_kiss=InteractionType.KISS in group.settings.allowed_interactions,
            allow_fuck=InteractionType.FUCK in group.settings.allowed_interactions,
            last_random_event_at=group.last_random_event_at,
        )
        self._session.add(model)
        await self._session.flush()
        return group

    async def update_settings(
        self, chat_id: TelegramChatId, settings: GroupSettings
    ) -> None:
        stmt = (
            update(GroupModel)
            .where(GroupModel.chat_id == int(chat_id))
            .values(
                battles_enabled=settings.battles_enabled,
                random_events_enabled=settings.random_events_enabled,
                random_event_interval_minutes=settings.random_event_interval_minutes,
                allow_pet=InteractionType.PET in settings.allowed_interactions,
                allow_kiss=InteractionType.KISS in settings.allowed_interactions,
                allow_fuck=InteractionType.FUCK in settings.allowed_interactions,
            )
        )
        await self._session.execute(stmt)

    async def list_with_random_events_ready(self, now: datetime) -> list[Group]:
        """
        Return groups where random events are enabled AND either never fired or
        the interval has elapsed. Filter in Python — the group set is small at
        current scale, and interval-arithmetic in SQL is fiddly across dialects.
        """
        stmt = select(GroupModel).where(GroupModel.random_events_enabled.is_(True))
        rows = (await self._session.scalars(stmt)).all()
        ready: list[Group] = []
        for m in rows:
            if m.last_random_event_at is None:
                ready.append(_to_entity(m))
                continue
            elapsed = now - m.last_random_event_at
            if elapsed >= timedelta(minutes=m.random_event_interval_minutes):
                ready.append(_to_entity(m))
        return ready

    async def mark_random_event_fired(
        self, chat_id: TelegramChatId, now: datetime
    ) -> None:
        stmt = (
            update(GroupModel)
            .where(GroupModel.chat_id == int(chat_id))
            .values(last_random_event_at=now)
        )
        await self._session.execute(stmt)


def _to_entity(model: GroupModel) -> Group:
    allowed: set[InteractionType] = set()
    if model.allow_pet:
        allowed.add(InteractionType.PET)
    if model.allow_kiss:
        allowed.add(InteractionType.KISS)
    if model.allow_fuck:
        allowed.add(InteractionType.FUCK)

    return Group(
        chat_id=TelegramChatId(model.chat_id),
        title=model.title,
        added_by_tg_id=(
            TelegramUserId(model.added_by_tg_id)
            if model.added_by_tg_id is not None
            else None
        ),
        created_at=model.created_at,
        settings=GroupSettings(
            battles_enabled=model.battles_enabled,
            random_events_enabled=model.random_events_enabled,
            random_event_interval_minutes=model.random_event_interval_minutes,
            allowed_interactions=frozenset(allowed),
        ),
        last_random_event_at=model.last_random_event_at,
    )
