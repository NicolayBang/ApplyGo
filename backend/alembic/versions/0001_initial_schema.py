"""Initial schema - canonical application record hub.

Revision ID: 0001
Revises:
Create Date: 2026-06-10
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # jobs
    # ------------------------------------------------------------------
    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_url", sa.String(2048), nullable=True),
        sa.Column("raw_text", sa.Text, nullable=True),
        sa.Column("title", sa.String(512), nullable=True),
        sa.Column("company", sa.String(256), nullable=True),
        sa.Column("location", sa.String(256), nullable=True),
        sa.Column("remote_ok", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("job_type", sa.String(64), nullable=True),
        sa.Column("ats_type", sa.String(64), nullable=True),
        sa.Column("salary_raw", sa.String(256), nullable=True),
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
    )
    op.create_index("ix_jobs_company", "jobs", ["company"])

    # ------------------------------------------------------------------
    # applications  (canonical hub record)
    # ------------------------------------------------------------------
    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("state", sa.String(64), nullable=False, server_default="discovered"),
        sa.Column(
            "automation_mode", sa.String(32), nullable=False, server_default="manual"
        ),
        sa.Column("fit_score", sa.Integer, nullable=True),
        sa.Column("confidence", sa.String(16), nullable=True),
        sa.Column("recommendation", sa.String(32), nullable=True),
        sa.Column("score_reasons", postgresql.JSONB, nullable=True),
        sa.Column("score_risks", postgresql.JSONB, nullable=True),
        sa.Column("missing_data", postgresql.JSONB, nullable=True),
        sa.Column("red_flags", postgresql.JSONB, nullable=True),
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
    )
    op.create_index("ix_applications_state", "applications", ["state"])
    op.create_index("ix_applications_job_id", "applications", ["job_id"])

    # ------------------------------------------------------------------
    # documents
    # ------------------------------------------------------------------
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("doc_type", sa.String(64), nullable=False),
        sa.Column("content", sa.Text, nullable=True),
        sa.Column("content_json", postgresql.JSONB, nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_documents_application_id", "documents", ["application_id"])

    # ------------------------------------------------------------------
    # email_threads
    # ------------------------------------------------------------------
    op.create_table(
        "email_threads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("external_thread_id", sa.String(256), nullable=True),
        sa.Column("subject", sa.String(512), nullable=True),
        sa.Column("direction", sa.String(16), nullable=False, server_default="inbound"),
        sa.Column("classification", sa.String(64), nullable=True),
        sa.Column("raw_body", sa.Text, nullable=True),
        sa.Column("draft_reply", sa.Text, nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_email_threads_application_id", "email_threads", ["application_id"]
    )

    # ------------------------------------------------------------------
    # policy_decisions
    # ------------------------------------------------------------------
    op.create_table(
        "policy_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("action_type", sa.String(64), nullable=False),
        sa.Column("mode", sa.String(32), nullable=False),
        sa.Column("allowed", sa.Boolean, nullable=False),
        sa.Column("reasons", postgresql.JSONB, nullable=True),
        sa.Column("risks", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_policy_decisions_application_id", "policy_decisions", ["application_id"]
    )

    # ------------------------------------------------------------------
    # executor_actions
    # ------------------------------------------------------------------
    op.create_table(
        "executor_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("idempotency_key", sa.String(256), nullable=False, unique=True),
        sa.Column("action_type", sa.String(64), nullable=False),
        sa.Column("execution_mode", sa.String(16), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="queued"),
        sa.Column("payload", postgresql.JSONB, nullable=True),
        sa.Column("result", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_executor_actions_application_id", "executor_actions", ["application_id"]
    )
    op.create_index(
        "ix_executor_actions_idempotency_key",
        "executor_actions",
        ["idempotency_key"],
    )

    # ------------------------------------------------------------------
    # event_log  (append-only - never updated or deleted)
    # ------------------------------------------------------------------
    op.create_table(
        "event_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("actor", sa.String(64), nullable=False, server_default="system"),
        sa.Column("from_state", sa.String(64), nullable=True),
        sa.Column("to_state", sa.String(64), nullable=True),
        sa.Column("payload", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_event_log_application_id", "event_log", ["application_id"])
    op.create_index("ix_event_log_event_type", "event_log", ["event_type"])
    op.create_index("ix_event_log_created_at", "event_log", ["created_at"])


def downgrade() -> None:
    op.drop_table("event_log")
    op.drop_table("executor_actions")
    op.drop_table("policy_decisions")
    op.drop_table("email_threads")
    op.drop_table("documents")
    op.drop_table("applications")
    op.drop_table("jobs")
