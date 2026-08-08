"""dick size change history, per user x chat

Revision ID: 0010
Revises: 0009
Create Date: 2026-08-08

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | Sequence[str] | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "dick_history",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("delta_cm", sa.Integer(), nullable=False),
        sa.Column("new_size_cm", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_dick_history_user_chat_created",
        "dick_history",
        ["user_id", "chat_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_dick_history_user_chat_created", table_name="dick_history")
    op.drop_table("dick_history")
