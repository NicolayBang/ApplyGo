"""Add policy decision outcome fields.

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "policy_decisions",
        sa.Column("decision", sa.String(16), nullable=False, server_default="review"),
    )
    op.add_column(
        "policy_decisions",
        sa.Column("required_overrides", postgresql.JSONB, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("policy_decisions", "required_overrides")
    op.drop_column("policy_decisions", "decision")
