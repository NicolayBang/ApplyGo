"""SQLAlchemy ORM models - canonical application record hub.

All entities attach to the Application record:
    Job  ->  Application  ->  Document
                          ->  EmailThread
                          ->  PolicyDecision
                          ->  ExecutorAction
                          ->  EventLogEntry
                          ->  ApplicationDocument
                          ->  ApplicationAnswer

M5 reusable document/answer model (additive, compatibility window):
    Document (logical library)  ->  DocumentVersion (immutable)
    DocumentVersion  <-  ApplicationDocument  ->  Application
    AnswerLibrary (current)  <-  ApplicationAnswer (immutable)  ->  Application
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
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from applypilot.db.base import Base
from applypilot.domain.state_machine import ApplicationState


# ---------------------------------------------------------------------------
# Company
# ---------------------------------------------------------------------------

class Company(Base):
    """Canonical company identity introduced for the M3 compatibility path."""

    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(256), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(256), nullable=True)
    normalized_domain: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    jobs: Mapped[list[Job]] = relationship(back_populates="company_identity")

    __table_args__ = (
        CheckConstraint("name <> ''", name="ck_companies_name_not_blank_m3"),
        CheckConstraint(
            "normalized_name <> ''",
            name="ck_companies_normalized_name_not_blank_m3",
        ),
        Index("ix_companies_normalized_name", "normalized_name"),
        Index("ix_companies_normalized_domain", "normalized_domain"),
        Index(
            "uq_companies_normalized_domain_m3",
            "normalized_domain",
            unique=True,
            postgresql_where=text("normalized_domain IS NOT NULL"),
        ),
        Index(
            "uq_companies_normalized_name_without_domain_m3",
            "normalized_name",
            unique=True,
            postgresql_where=text("normalized_domain IS NULL"),
        ),
    )


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
    company_source_text: Mapped[str | None] = mapped_column(String(256), nullable=True)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False
    )
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
    company_identity: Mapped[Company | None] = relationship(back_populates="jobs")

    __table_args__ = (
        Index("ix_jobs_company_source_text", "company_source_text"),
        Index("ix_jobs_company_id", "company_id"),
    )

    @property
    def company(self) -> str | None:
        """Return the canonical display company while preserving legacy API compatibility."""
        return self.company_identity.name if self.company_identity else self.company_source_text


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
    packet_reviews: Mapped[list[ApplicationPacketReview]] = relationship(
        back_populates="application", passive_deletes="all"
    )
    events: Mapped[list[EventLogEntry]] = relationship(
        back_populates="application", passive_deletes="all"
    )
    application_documents: Mapped[list[ApplicationDocument]] = relationship(
        back_populates="application", passive_deletes="all"
    )
    application_answers: Mapped[list[ApplicationAnswer]] = relationship(
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
    """Reusable logical document library (M5).

    The implemented M1 placeholder is transformed in place into the stable logical
    identity of a document. A ``documents`` row owns no content directly; content lives
    only in immutable ``document_versions`` rows. The legacy single-application columns
    (``application_id`` cascade, ``content``, ``content_json``, ``version``) are retained
    during the M5 compatibility window and are removed only by a later PR.
    """

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    doc_type: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    is_archived: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false"), nullable=False
    )

    # Retained legacy single-application columns (compatibility window; removed in a later PR).
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    application: Mapped[Application] = relationship(back_populates="documents")
    versions: Mapped[list[DocumentVersion]] = relationship(
        back_populates="document", passive_deletes="all"
    )

    __table_args__ = (
        CheckConstraint(
            "doc_type IN ('resume', 'cover_letter', 'supporting', 'other')",
            name="ck_documents_doc_type_m5",
        ),
        CheckConstraint("name <> ''", name="ck_documents_name_not_blank_m5"),
        Index("ix_documents_application_id", "application_id"),
        Index("ix_documents_doc_type", "doc_type"),
        Index("ix_documents_is_archived", "is_archived"),
    )


# ---------------------------------------------------------------------------
# DocumentVersion  (immutable rendered version)
# ---------------------------------------------------------------------------

class DocumentVersion(Base):
    """Frozen, immutable rendering of one logical document (M5).

    Never updated after insert; corrections append a new version. There is no
    ``updated_at`` and no path mutates content, version_number, or checksum.
    """

    __tablename__ = "document_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="RESTRICT"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    document: Mapped[Document] = relationship(back_populates="versions")
    application_links: Mapped[list[ApplicationDocument]] = relationship(
        back_populates="document_version", passive_deletes="all"
    )

    __table_args__ = (
        CheckConstraint(
            "version_number > 0",
            name="ck_document_versions_version_positive_m5",
        ),
        CheckConstraint(
            "content IS NOT NULL OR content_json IS NOT NULL",
            name="ck_document_versions_payload_present_m5",
        ),
        Index("ix_document_versions_document_id", "document_id"),
        Index("ix_document_versions_checksum", "checksum"),
        Index(
            "uq_document_versions_document_id_version_number_m5",
            "document_id",
            "version_number",
            unique=True,
        ),
    )


# ---------------------------------------------------------------------------
# ApplicationDocument  (append-only attachment of an exact version)
# ---------------------------------------------------------------------------

class ApplicationDocument(Base):
    """Append-only attachment binding one exact document version to one application (M5).

    Binds an exact ``document_version_id`` and never silently upgrades. Attaching a newer
    version is a new row. ``ON DELETE RESTRICT`` on both FKs preserves attachment history.
    """

    __tablename__ = "application_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="RESTRICT"),
        nullable=False,
    )
    document_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_versions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(64), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    application: Mapped[Application] = relationship(back_populates="application_documents")
    document_version: Mapped[DocumentVersion] = relationship(
        back_populates="application_links"
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('resume', 'cover_letter', 'supporting', 'other')",
            name="ck_application_documents_role_m5",
        ),
        CheckConstraint(
            "display_order >= 0",
            name="ck_application_documents_display_order_non_negative_m5",
        ),
        Index("ix_application_documents_application_id", "application_id"),
        Index("ix_application_documents_document_version_id", "document_version_id"),
        Index(
            "uq_application_documents_app_version_role_m5",
            "application_id",
            "document_version_id",
            "role",
            unique=True,
        ),
    )


# ---------------------------------------------------------------------------
# AnswerLibrary  (current reusable answers)
# ---------------------------------------------------------------------------

class AnswerLibrary(Base):
    """Current, reusable question/answer record (M5).

    Library answers are mutable (edit/archive in place); historical truth is preserved
    separately in immutable ``application_answers`` snapshots, never by mutating the library.
    """

    __tablename__ = "answer_library"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    question_key: Mapped[str] = mapped_column(String(256), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_archived: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    application_answers: Mapped[list[ApplicationAnswer]] = relationship(
        back_populates="answer_library_entry", passive_deletes="all"
    )

    __table_args__ = (
        CheckConstraint(
            "question_key <> ''",
            name="ck_answer_library_question_key_not_blank_m5",
        ),
        Index("ix_answer_library_question_key", "question_key"),
        Index("ix_answer_library_is_archived", "is_archived"),
        Index(
            "uq_answer_library_question_key_active_m5",
            "question_key",
            unique=True,
            postgresql_where=text("is_archived IS false"),
        ),
    )


# ---------------------------------------------------------------------------
# ApplicationAnswer  (immutable answer snapshot)
# ---------------------------------------------------------------------------

class ApplicationAnswer(Base):
    """Immutable per-application answer snapshot with optional library provenance (M5).

    A row is the immutable question/answer used by an application. A later edit or archive
    of the referenced library row never changes this snapshot. ``ON DELETE RESTRICT`` on
    ``answer_library_id`` preserves provenance.
    """

    __tablename__ = "application_answers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="RESTRICT"),
        nullable=False,
    )
    answer_library_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("answer_library.id", ondelete="RESTRICT"),
        nullable=True,
    )
    question_key: Mapped[str] = mapped_column(String(256), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    application: Mapped[Application] = relationship(back_populates="application_answers")
    answer_library_entry: Mapped[AnswerLibrary | None] = relationship(
        back_populates="application_answers"
    )

    __table_args__ = (
        CheckConstraint(
            "question_key <> ''",
            name="ck_application_answers_question_key_not_blank_m5",
        ),
        Index("ix_application_answers_application_id", "application_id"),
        Index("ix_application_answers_answer_library_id", "answer_library_id"),
        Index(
            "uq_application_answers_app_question_key_m5",
            "application_id",
            "question_key",
            unique=True,
        ),
    )


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
# ApplicationPacketReview
# ---------------------------------------------------------------------------

class ApplicationPacketReview(Base):
    """Human packet review evidence for M2 packet persistence."""

    __tablename__ = "application_packet_reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id"),
        nullable=False,
    )
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    reviewed_by: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    packet_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    application: Mapped[Application] = relationship(back_populates="packet_reviews")

    __table_args__ = (
        CheckConstraint(
            "decision IN ('approved', 'rejected', 'changes_requested')",
            name="ck_application_packet_reviews_decision_m2",
        ),
        CheckConstraint(
            "source IN ('dashboard')",
            name="ck_application_packet_reviews_source_m2",
        ),
        Index("ix_application_packet_reviews_application_id", "application_id"),
        Index("ix_application_packet_reviews_created_at", "created_at"),
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
