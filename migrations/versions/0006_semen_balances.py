"""semen balances per user × chat

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-01

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | Sequence[str] | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "semen_balances",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("stored_ml", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "chat_id", name="uq_semen_user_chat"),
    )
    op.create_index("ix_semen_balances_chat_id", "semen_balances", ["chat_id"])


def downgrade() -> None:
    op.drop_index("ix_semen_balances_chat_id", table_name="semen_balances")
    op.drop_table("semen_balances")
