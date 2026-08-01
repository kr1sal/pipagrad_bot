from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dishka import AsyncContainer

from src.application.use_cases.resolve_pending_events import (
    ResolvePendingEventsUseCase,
)
from src.application.use_cases.trigger_random_events import (
    TriggerRandomEventsCycleUseCase,
)

log = logging.getLogger(__name__)


class RandomEventsScheduler:
    """
    Wraps APScheduler with two jobs:
      * random-events-tick: rolls new events per ready group
      * pending-resolve-tick: finalizes pending events past their timer

    Both open a fresh dishka REQUEST scope per tick so each use case gets its
    own UnitOfWork (a scoped session), preventing session reuse across ticks.
    """

    def __init__(
        self,
        container: AsyncContainer,
        random_tick_seconds: int = 60,
        pending_tick_seconds: int = 30,
    ) -> None:
        self._container = container
        self._random_tick_seconds = random_tick_seconds
        self._pending_tick_seconds = pending_tick_seconds
        self._scheduler = AsyncIOScheduler()

    def start(self) -> None:
        self._scheduler.add_job(
            self._tick_random,
            trigger=IntervalTrigger(seconds=self._random_tick_seconds),
            id="random-events-tick",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        self._scheduler.add_job(
            self._tick_pending,
            trigger=IntervalTrigger(seconds=self._pending_tick_seconds),
            id="pending-resolve-tick",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        self._scheduler.start()

    def shutdown(self) -> None:
        self._scheduler.shutdown(wait=False)

    async def _tick_random(self) -> None:
        try:
            async with self._container() as request_scope:
                use_case = await request_scope.get(TriggerRandomEventsCycleUseCase)
                fired = await use_case.execute()
                if fired:
                    log.info("random-events tick fired=%d", fired)
        except Exception:  # noqa: BLE001
            log.exception("random-events tick crashed")

    async def _tick_pending(self) -> None:
        try:
            async with self._container() as request_scope:
                use_case = await request_scope.get(ResolvePendingEventsUseCase)
                resolved = await use_case.execute()
                if resolved:
                    log.info("pending-resolve tick resolved=%d", resolved)
        except Exception:  # noqa: BLE001
            log.exception("pending-resolve tick crashed")
