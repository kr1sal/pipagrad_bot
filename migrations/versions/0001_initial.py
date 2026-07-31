"""initial: users + dicks

Revision ID: 0001
Revises:
Create Date: 2026-07-31

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tg_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tg_id", name="uq_users_tg_id"),
    )
    op.create_index("ix_users_tg_id", "users", ["tg_id"])

    op.create_table(
        "dicks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("size_cm", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_grow_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("user_id", "chat_id", name="uq_dicks_user_chat"),
    )
    op.create_index("ix_dicks_chat_id", "dicks", ["chat_id"])


def downgrade() -> None:
    op.drop_index("ix_dicks_chat_id", table_name="dicks")
    op.drop_table("dicks")
    op.drop_index("ix_users_tg_id", table_name="users")
    op.drop_table("users")
