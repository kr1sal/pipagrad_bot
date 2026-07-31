"""user preferences per chat

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-01

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_preferences",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("allow_pet", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("allow_kiss", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("allow_fuck", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("user_id", "chat_id", name="uq_prefs_user_chat"),
    )
    op.create_index(
        "ix_user_preferences_chat_id", "user_preferences", ["chat_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_user_preferences_chat_id", table_name="user_preferences")
    op.drop_table("user_preferences")
