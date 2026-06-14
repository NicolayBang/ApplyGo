"""Add executor contract metadata.

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-14
"""

from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.add_column(
        "executor_actions",
        sa.Column(
            "request_id",
            sa.UUID(),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
    )
    op.add_column(
        "executor_actions",
        sa.Column("worker", sa.String(length=32), nullable=False, server_default="email"),
    )
    op.add_column(
        "executor_actions",
        sa.Column(
            "requested_by",
            sa.String(length=64),
            nullable=False,
            server_default="system",
        ),
    )
    op.add_column(
        "executor_actions",
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_unique_constraint(
        "uq_executor_actions_request_id",
        "executor_actions",
        ["request_id"],
    )
    op.create_index(
        "ix_executor_actions_request_id",
        "executor_actions",
        ["request_id"],
    )

    op.alter_column("executor_actions", "request_id", server_default=None)
    op.alter_column("executor_actions", "worker", server_default=None)
    op.alter_column("executor_actions", "requested_by", server_default=None)
    op.alter_column("executor_actions", "requested_at", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_executor_actions_request_id", table_name="executor_actions")
    op.drop_constraint(
        "uq_executor_actions_request_id",
        "executor_actions",
        type_="unique",
    )
    op.drop_column("executor_actions", "requested_at")
    op.drop_column("executor_actions", "requested_by")
    op.drop_column("executor_actions", "worker")
    op.drop_column("executor_actions", "request_id")
