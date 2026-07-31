"""groups + settings

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-31

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "groups",
        sa.Column("chat_id", sa.BigInteger(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("added_by_tg_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("battles_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "random_events_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "random_event_interval_minutes",
            sa.Integer(),
            nullable=False,
            server_default="60",
        ),
        sa.Column("allow_pet", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("allow_kiss", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("allow_fuck", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_table("groups")
