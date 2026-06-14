"""Add M1 value check constraints.

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-14
"""

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


CHECKS = (
    (
        "ck_applications_state_m1",
        "applications",
        "state IN ("
        "'ApplicationCreated', 'Draft', 'ReadyForReview', 'Approved', "
        "'Submitted', 'Rejected', 'Archived'"
        ")",
    ),
    (
        "ck_applications_automation_mode_m1",
        "applications",
        "automation_mode IN ('manual', 'dry_run', 'semi_auto', 'full_auto')",
    ),
    (
        "ck_policy_decisions_mode_m1",
        "policy_decisions",
        "mode IN ('manual', 'dry_run', 'semi_auto', 'full_auto')",
    ),
    (
        "ck_policy_decisions_decision_m1",
        "policy_decisions",
        "decision IN ('allow', 'deny', 'review')",
    ),
    (
        "ck_executor_actions_execution_mode_m1",
        "executor_actions",
        "execution_mode IN ('dry_run', 'execute')",
    ),
    (
        "ck_executor_actions_status_m1",
        "executor_actions",
        "status IN ("
        "'planned', 'queued', 'completed', 'failed', 'blocked', "
        "'not_implemented'"
        ")",
    ),
    (
        "ck_executor_actions_worker_m1",
        "executor_actions",
        "worker IN ('email', 'browser', 'documents')",
    ),
    (
        "ck_email_threads_direction_m1",
        "email_threads",
        "direction IN ('inbound', 'outbound')",
    ),
)


def upgrade() -> None:
    op.execute(
        "UPDATE applications SET state = 'ApplicationCreated' WHERE state = 'discovered'"
    )

    for name, table_name, condition in CHECKS:
        op.create_check_constraint(name, table_name, condition)


def downgrade() -> None:
    for name, table_name, _condition in reversed(CHECKS):
        op.drop_constraint(name, table_name, type_="check")
