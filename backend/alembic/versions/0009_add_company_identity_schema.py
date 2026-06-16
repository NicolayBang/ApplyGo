"""Add company identity schema.

Revision ID: 0009
Revises: 0008
Create Date: 2026-06-15
"""

from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("normalized_name", sa.String(length=256), nullable=False),
        sa.Column("domain", sa.String(length=256), nullable=True),
        sa.Column("normalized_domain", sa.String(length=256), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("name <> ''", name="ck_companies_name_not_blank_m3"),
        sa.CheckConstraint(
            "normalized_name <> ''",
            name="ck_companies_normalized_name_not_blank_m3",
        ),
    )
    op.create_index("ix_companies_normalized_name", "companies", ["normalized_name"])
    op.create_index("ix_companies_normalized_domain", "companies", ["normalized_domain"])
    op.create_index(
        "uq_companies_normalized_domain_m3",
        "companies",
        ["normalized_domain"],
        unique=True,
        postgresql_where=sa.text("normalized_domain IS NOT NULL"),
    )
    op.create_index(
        "uq_companies_normalized_name_without_domain_m3",
        "companies",
        ["normalized_name"],
        unique=True,
        postgresql_where=sa.text("normalized_domain IS NULL"),
    )

    op.add_column("jobs", sa.Column("company_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "jobs_company_id_fkey",
        "jobs",
        "companies",
        ["company_id"],
        ["id"],
    )
    op.create_index("ix_jobs_company_id", "jobs", ["company_id"])


def downgrade() -> None:
    op.drop_index("ix_jobs_company_id", table_name="jobs")
    op.drop_constraint("jobs_company_id_fkey", "jobs", type_="foreignkey")
    op.drop_column("jobs", "company_id")

    op.drop_index(
        "uq_companies_normalized_name_without_domain_m3",
        table_name="companies",
    )
    op.drop_index("uq_companies_normalized_domain_m3", table_name="companies")
    op.drop_index("ix_companies_normalized_domain", table_name="companies")
    op.drop_index("ix_companies_normalized_name", table_name="companies")
    op.drop_table("companies")
