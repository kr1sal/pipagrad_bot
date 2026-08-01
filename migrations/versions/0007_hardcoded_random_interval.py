"""hardcoded random-event interval: drop configurable minutes, rename last→next

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-01

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | Sequence[str] | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("groups", "random_event_interval_minutes")
    op.alter_column(
        "groups",
        "last_random_event_at",
        new_column_name="next_random_event_at",
    )


def downgrade() -> None:
    op.alter_column(
        "groups",
        "next_random_event_at",
        new_column_name="last_random_event_at",
    )
    op.add_column(
        "groups",
        sa.Column(
            "random_event_interval_minutes",
            sa.Integer(),
            nullable=False,
            server_default="60",
        ),
    )
