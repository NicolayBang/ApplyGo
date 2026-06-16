"""Complete company identity cutover.

Revision ID: 0011
Revises: 0010
Create Date: 2026-06-15
"""

from alembic import op
import sqlalchemy as sa

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("jobs", "company_id", existing_type=sa.UUID(), nullable=False)
    op.drop_index("ix_jobs_company", table_name="jobs")
    op.alter_column(
        "jobs",
        "company",
        new_column_name="company_source_text",
        existing_type=sa.String(length=256),
        existing_nullable=True,
    )
    op.create_index(
        "ix_jobs_company_source_text",
        "jobs",
        ["company_source_text"],
    )


def downgrade() -> None:
    op.drop_index("ix_jobs_company_source_text", table_name="jobs")
    op.alter_column(
        "jobs",
        "company_source_text",
        new_column_name="company",
        existing_type=sa.String(length=256),
        existing_nullable=True,
    )
    op.create_index("ix_jobs_company", "jobs", ["company"])
    op.alter_column("jobs", "company_id", existing_type=sa.UUID(), nullable=True)
