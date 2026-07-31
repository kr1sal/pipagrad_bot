from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dishka import AsyncContainer

from src.application.use_cases.trigger_random_events import (
    TriggerRandomEventsCycleUseCase,
)

log = logging.getLogger(__name__)


class RandomEventsScheduler:
    """
    Wraps APScheduler and drives one job that ticks every `tick_seconds` seconds.
    Each tick resolves a fresh REQUEST scope from the DI container so the use
    case gets its own UnitOfWork (a scoped session), preventing session reuse
    across ticks.
    """

    def __init__(self, container: AsyncContainer, tick_seconds: int = 60) -> None:
        self._container = container
        self._tick_seconds = tick_seconds
        self._scheduler = AsyncIOScheduler()

    def start(self) -> None:
        self._scheduler.add_job(
            self._tick,
            trigger=IntervalTrigger(seconds=self._tick_seconds),
            id="random-events-tick",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        self._scheduler.start()

    def shutdown(self) -> None:
        self._scheduler.shutdown(wait=False)

    async def _tick(self) -> None:
        try:
            async with self._container() as request_scope:
                use_case = await request_scope.get(TriggerRandomEventsCycleUseCase)
                fired = await use_case.execute()
                if fired:
                    log.info("random events tick fired=%d", fired)
        except Exception:  # noqa: BLE001
            log.exception("random-events tick crashed")
