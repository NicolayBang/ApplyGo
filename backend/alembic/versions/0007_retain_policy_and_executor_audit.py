"""Retain policy and executor audit records.

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-14
"""

from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "policy_decisions_application_id_fkey",
        "policy_decisions",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "policy_decisions_application_id_fkey",
        "policy_decisions",
        "applications",
        ["application_id"],
        ["id"],
    )

    op.drop_constraint(
        "executor_actions_application_id_fkey",
        "executor_actions",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "executor_actions_application_id_fkey",
        "executor_actions",
        "applications",
        ["application_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "executor_actions_application_id_fkey",
        "executor_actions",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "executor_actions_application_id_fkey",
        "executor_actions",
        "applications",
        ["application_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint(
        "policy_decisions_application_id_fkey",
        "policy_decisions",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "policy_decisions_application_id_fkey",
        "policy_decisions",
        "applications",
        ["application_id"],
        ["id"],
        ondelete="CASCADE",
    )
