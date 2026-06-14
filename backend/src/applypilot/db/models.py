"""SQLAlchemy ORM models - canonical application record hub.

All entities attach to the Application record:
    Job  ->  Application  ->  Document
                          ->  EmailThread
                          ->  PolicyDecision
                          ->  ExecutorAction
                          ->  EventLogEntry
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    UUID,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from applypilot.db.base import Base
from applypilot.domain.state_machine import ApplicationState


# ---------------------------------------------------------------------------
# Job
# ---------------------------------------------------------------------------

class Job(Base):
    """A normalized job posting. Source of truth for role details."""

    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    company: Mapped[str | None] = mapped_column(String(256), nullable=True)
    location: Mapped[str | None] = mapped_column(String(256), nullable=True)
    remote_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    job_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ats_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    salary_raw: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    applications: Mapped[list[Application]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_jobs_company", "company"),)


# ---------------------------------------------------------------------------
# Application  (canonical hub record)
# ---------------------------------------------------------------------------

class Application(Base):
    """The canonical application record. Every other entity links here."""

    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )

    # Workflow
    state: Mapped[str] = mapped_column(
        String(64),
        default=ApplicationState.APPLICATION_CREATED.value,
        server_default=ApplicationState.APPLICATION_CREATED.value,
        nullable=False,
    )
    automation_mode: Mapped[str] = mapped_column(String(32), default="manual", nullable=False)

    # Scoring / explanation (confidence and explanation schema from locked plan)
    fit_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(16), nullable=True)
    recommendation: Mapped[str | None] = mapped_column(String(32), nullable=True)
    score_reasons: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    score_risks: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    missing_data: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    red_flags: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships back to hub entities
    job: Mapped[Job] = relationship(back_populates="applications")
    documents: Mapped[list[Document]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )
    email_threads: Mapped[list[EmailThread]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )
    policy_decisions: Mapped[list[PolicyDecision]] = relationship(
        back_populates="application", passive_deletes="all"
    )
    executor_actions: Mapped[list[ExecutorAction]] = relationship(
        back_populates="application", passive_deletes="all"
    )
    events: Mapped[list[EventLogEntry]] = relationship(
        back_populates="application", passive_deletes="all"
    )

    __table_args__ = (
        CheckConstraint(
            "state IN ("
            "'ApplicationCreated', 'Draft', 'ReadyForReview', 'Approved', "
            "'Submitted', 'Rejected', 'Archived'"
            ")",
            name="ck_applications_state_m1",
        ),
        CheckConstraint(
            "automation_mode IN ('manual', 'dry_run', 'semi_auto', 'full_auto')",
            name="ck_applications_automation_mode_m1",
        ),
        Index("ix_applications_state", "state"),
        Index("ix_applications_job_id", "job_id"),
    )


# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------

class Document(Base):
    """Generated application documents: CV bullets, cover note, screening answers."""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    doc_type: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    application: Mapped[Application] = relationship(back_populates="documents")

    __table_args__ = (Index("ix_documents_application_id", "application_id"),)


# ---------------------------------------------------------------------------
# EmailThread
# ---------------------------------------------------------------------------

class EmailThread(Base):
    """Inbound or outbound recruiter email threads tied to an application."""

    __tablename__ = "email_threads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    external_thread_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    subject: Mapped[str | None] = mapped_column(String(512), nullable=True)
    direction: Mapped[str] = mapped_column(String(16), default="inbound", nullable=False)
    classification: Mapped[str | None] = mapped_column(String(64), nullable=True)
    raw_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    draft_reply: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    application: Mapped[Application] = relationship(back_populates="email_threads")

    __table_args__ = (
        CheckConstraint(
            "direction IN ('inbound', 'outbound')",
            name="ck_email_threads_direction_m1",
        ),
        Index("ix_email_threads_application_id", "application_id"),
    )


# ---------------------------------------------------------------------------
# PolicyDecision
# ---------------------------------------------------------------------------

class PolicyDecision(Base):
    """Logged policy gate evaluation. Recorded before any executor action."""

    __tablename__ = "policy_decisions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id"),
        nullable=False,
    )
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    mode: Mapped[str] = mapped_column(String(32), nullable=False)
    decision: Mapped[str] = mapped_column(String(16), default="review", nullable=False)
    allowed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reasons: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    risks: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    required_overrides: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    application: Mapped[Application] = relationship(back_populates="policy_decisions")

    __table_args__ = (
        CheckConstraint(
            "mode IN ('manual', 'dry_run', 'semi_auto', 'full_auto')",
            name="ck_policy_decisions_mode_m1",
        ),
        CheckConstraint(
            "decision IN ('allow', 'deny', 'review')",
            name="ck_policy_decisions_decision_m1",
        ),
        Index("ix_policy_decisions_application_id", "application_id"),
    )


# ---------------------------------------------------------------------------
# ExecutorAction
# ---------------------------------------------------------------------------

class ExecutorAction(Base):
    """Execution record for every executor dispatch (execute or dry_run).

    Idempotency key prevents duplicate actions on retry.
    Audit sequence: policy_decision -> executor_action (attempt) -> result logged -> state updated.
    """

    __tablename__ = "executor_actions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id"),
        nullable=False,
    )
    worker: Mapped[str] = mapped_column(String(32), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    execution_mode: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False)
    requested_by: Mapped[str] = mapped_column(String(64), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    application: Mapped[Application] = relationship(back_populates="executor_actions")

    __table_args__ = (
        CheckConstraint(
            "execution_mode IN ('dry_run', 'execute')",
            name="ck_executor_actions_execution_mode_m1",
        ),
        CheckConstraint(
            "status IN ("
            "'planned', 'queued', 'completed', 'failed', 'blocked', "
            "'not_implemented'"
            ")",
            name="ck_executor_actions_status_m1",
        ),
        CheckConstraint(
            "worker IN ('email', 'browser', 'documents')",
            name="ck_executor_actions_worker_m1",
        ),
        Index("ix_executor_actions_application_id", "application_id"),
        Index("ix_executor_actions_request_id", "request_id"),
        Index("ix_executor_actions_idempotency_key", "idempotency_key"),
    )


# ---------------------------------------------------------------------------
# EventLogEntry  (append-only)
# ---------------------------------------------------------------------------

class EventLogEntry(Base):
    """Append-only event log. Never updated or deleted.

    Schema: id, application_id, event_type, actor, from_state, to_state, payload, created_at
    Records state transitions, policy decisions, executor attempts, and results.
    """

    __tablename__ = "event_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    actor: Mapped[str] = mapped_column(String(64), default="system", nullable=False)
    from_state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    to_state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    application: Mapped[Application] = relationship(back_populates="events")

    __table_args__ = (
        Index("ix_event_log_application_id", "application_id"),
        Index("ix_event_log_event_type", "event_type"),
        Index("ix_event_log_created_at", "created_at"),
    )
