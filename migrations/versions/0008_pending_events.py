"""pending events (orgy, bot battle)

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-01

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0008"
down_revision: str | Sequence[str] | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pending_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("chat_message_id", sa.BigInteger(), nullable=False),
        sa.Column("resolves_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("ix_pending_events_chat_id", "pending_events", ["chat_id"])
    op.create_index("ix_pending_events_resolves_at", "pending_events", ["resolves_at"])


def downgrade() -> None:
    op.drop_index("ix_pending_events_resolves_at", table_name="pending_events")
    op.drop_index("ix_pending_events_chat_id", table_name="pending_events")
    op.drop_table("pending_events")
