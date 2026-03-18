"""create outbox_messages table

Revision ID: 003
Revises: 002
Create Date: 2026-03-18
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "outbox_messages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("payload", JSONB(), nullable=False),
        sa.Column("published", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_outbox_messages_published",
        "outbox_messages",
        ["published"],
        postgresql_where=sa.text("published = false"),
    )


def downgrade() -> None:
    op.drop_index("ix_outbox_messages_published", "outbox_messages")
    op.drop_table("outbox_messages")
