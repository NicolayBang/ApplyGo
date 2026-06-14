"""Align application state default with M1 state machine.

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-14
"""

from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "applications",
        "state",
        existing_type=sa.String(length=64),
        existing_nullable=False,
        server_default="ApplicationCreated",
    )


def downgrade() -> None:
    op.alter_column(
        "applications",
        "state",
        existing_type=sa.String(length=64),
        existing_nullable=False,
        server_default="discovered",
    )
