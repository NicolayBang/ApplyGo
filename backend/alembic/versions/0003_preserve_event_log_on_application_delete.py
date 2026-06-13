"""Preserve event log rows when applications are deleted.

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-13
"""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "event_log_application_id_fkey",
        "event_log",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "event_log_application_id_fkey",
        "event_log",
        "applications",
        ["application_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "event_log_application_id_fkey",
        "event_log",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "event_log_application_id_fkey",
        "event_log",
        "applications",
        ["application_id"],
        ["id"],
        ondelete="CASCADE",
    )
