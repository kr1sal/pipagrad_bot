"""
One-off migration: fold legacy per-DM dick/semen rows into the shared global
bucket.

Before the global-scope change, a private chat with the bot stored its own
row keyed by chat_id == the user's own tg_id — separate from the global
bucket (chat_id=GLOBAL_CHAT_ID) that inline-mode interactions already used.
Now DMs read/write the same global bucket as inline mode, so any pre-existing
DM row is stranded under a chat_id nothing queries anymore. This script folds
each stranded DM row into the global bucket (taking the larger/more current
value so nobody loses progress) and removes the now-redundant DM row.

Safe to re-run: once a user's DM row has been folded in, there's nothing left
to migrate for them.

Usage:
    .venv/bin/python scripts/migrate_dm_to_global.py --dry-run   # preview
    .venv/bin/python scripts/migrate_dm_to_global.py             # apply
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.domain.entities.semen_balance import SemenBalance, SemenConfig
from src.domain.value_objects.telegram_ids import GLOBAL_CHAT_ID
from src.infrastructure.config.settings import Settings
from src.infrastructure.persistence.models import (
    DickModel,
    SemenBalanceModel,
    UserModel,
)

log = logging.getLogger("migrate_dm_to_global")


async def _merge_dick(session, user: UserModel, dry_run: bool) -> int | None:
    """Returns the user's resulting global dick size (for the semen cap calc
    that follows), or None if the user has no dick row at all."""
    dm_dick = await session.scalar(
        select(DickModel).where(
            DickModel.user_id == user.id, DickModel.chat_id == user.tg_id
        )
    )
    global_dick = await session.scalar(
        select(DickModel).where(
            DickModel.user_id == user.id,
            DickModel.chat_id == int(GLOBAL_CHAT_ID),
        )
    )

    if dm_dick is None:
        return global_dick.size_cm if global_dick is not None else None

    if global_dick is None:
        log.info(
            "user %s: moving DM dick (%d cm) -> global (no prior global row)",
            user.tg_id, dm_dick.size_cm,
        )
        if not dry_run:
            dm_dick.chat_id = int(GLOBAL_CHAT_ID)
        return dm_dick.size_cm

    merged_size = max(global_dick.size_cm, dm_dick.size_cm)
    merged_last_grow = max(
        (t for t in (global_dick.last_grow_at, dm_dick.last_grow_at) if t is not None),
        default=None,
    )
    log.info(
        "user %s: merging DM dick (%d cm) into global (%d cm) -> %d cm",
        user.tg_id, dm_dick.size_cm, global_dick.size_cm, merged_size,
    )
    if not dry_run:
        global_dick.size_cm = merged_size
        global_dick.last_grow_at = merged_last_grow
        await session.delete(dm_dick)
    return merged_size


async def _merge_semen(
    session,
    user: UserModel,
    global_size_cm: int | None,
    semen_cfg: SemenConfig,
    now: datetime,
    dry_run: bool,
) -> None:
    dm_semen = await session.scalar(
        select(SemenBalanceModel).where(
            SemenBalanceModel.user_id == user.id,
            SemenBalanceModel.chat_id == user.tg_id,
        )
    )
    if dm_semen is None:
        return

    global_semen = await session.scalar(
        select(SemenBalanceModel).where(
            SemenBalanceModel.user_id == user.id,
            SemenBalanceModel.chat_id == int(GLOBAL_CHAT_ID),
        )
    )

    cap = semen_cfg.cap_for(global_size_cm or 0)
    dm_current = SemenBalance(
        id=None, user_id=user.id, chat_id=user.tg_id,
        stored_ml=dm_semen.stored_ml, updated_at=dm_semen.updated_at,
    ).current_ml(now, semen_cfg.regen_per_hour, cap)

    if global_semen is None:
        log.info(
            "user %s: moving DM semen (%d ml projected) -> global",
            user.tg_id, dm_current,
        )
        if not dry_run:
            dm_semen.chat_id = int(GLOBAL_CHAT_ID)
            dm_semen.stored_ml = dm_current
            dm_semen.updated_at = now
        return

    global_current = SemenBalance(
        id=None, user_id=user.id, chat_id=int(GLOBAL_CHAT_ID),
        stored_ml=global_semen.stored_ml, updated_at=global_semen.updated_at,
    ).current_ml(now, semen_cfg.regen_per_hour, cap)

    merged = max(dm_current, global_current)
    log.info(
        "user %s: merging DM semen (%d ml) into global (%d ml) -> %d ml",
        user.tg_id, dm_current, global_current, merged,
    )
    if not dry_run:
        global_semen.stored_ml = merged
        global_semen.updated_at = now
        await session.delete(dm_semen)


async def run(dry_run: bool) -> None:
    settings = Settings()
    semen_cfg = SemenConfig(
        base_cap_ml=settings.semen_base_cap_ml,
        cap_per_cm=settings.semen_cap_per_cm,
        regen_per_hour=settings.semen_regen_per_hour,
        fuck_cost_ml=settings.fuck_cost_ml,
    )
    now = datetime.now(timezone.utc)

    engine = create_async_engine(settings.postgres_dsn)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        users = (await session.scalars(select(UserModel))).all()
        log.info("scanning %d users for stranded DM rows%s", len(users), " (dry run)" if dry_run else "")

        for user in users:
            global_size_cm = await _merge_dick(session, user, dry_run)
            await _merge_semen(session, user, global_size_cm, semen_cfg, now, dry_run)

        if dry_run:
            await session.rollback()
            log.info("dry run complete — no changes written")
        else:
            await session.commit()
            log.info("migration complete")

    await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true", help="log what would change, write nothing"
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    asyncio.run(run(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
