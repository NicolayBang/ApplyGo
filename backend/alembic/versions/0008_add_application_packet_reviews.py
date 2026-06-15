"""Add application packet reviews.

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-15
"""

from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "application_packet_reviews",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "application_id",
            sa.UUID(),
            sa.ForeignKey("applications.id"),
            nullable=False,
        ),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("reviewed_by", sa.String(length=64), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("packet_text", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "decision IN ('approved', 'rejected', 'changes_requested')",
            name="ck_application_packet_reviews_decision_m2",
        ),
        sa.CheckConstraint(
            "source IN ('dashboard')",
            name="ck_application_packet_reviews_source_m2",
        ),
    )
    op.create_index(
        "ix_application_packet_reviews_application_id",
        "application_packet_reviews",
        ["application_id"],
    )
    op.create_index(
        "ix_application_packet_reviews_created_at",
        "application_packet_reviews",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_application_packet_reviews_created_at",
        table_name="application_packet_reviews",
    )
    op.drop_index(
        "ix_application_packet_reviews_application_id",
        table_name="application_packet_reviews",
    )
    op.drop_table("application_packet_reviews")
