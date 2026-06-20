"""Domain schemas for the canonical application record.

These Pydantic models are used at the API layer.
SQLAlchemy ORM models live in applypilot.db.models.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator, model_validator

from applypilot.domain.executor.schemas import ExecutorActionRead
from applypilot.domain.policy.schemas import PolicyDecisionRead
from applypilot.domain.state_machine.states import ApplicationState


# ---------------------------------------------------------------------------
# Job schemas
# ---------------------------------------------------------------------------

class JobCreate(BaseModel):
    source_url: str | None = None
    raw_text: str | None = None
    title: str | None = None
    company: str | None = None
    location: str | None = None
    remote_ok: bool = False
    job_type: str | None = None
    ats_type: str | None = None
    salary_raw: str | None = None

    @field_validator(
        "title",
        "company",
        "location",
        "job_type",
        "ats_type",
        "salary_raw",
        mode="before",
    )
    @classmethod
    def _normalize_short_text(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        normalized = re.sub(r"\s+", " ", value).strip()
        return normalized or None

    @field_validator("raw_text", mode="before")
    @classmethod
    def _normalize_raw_text(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        normalized = value.replace("\r\n", "\n").replace("\r", "\n").strip()
        return normalized or None

    @field_validator("source_url", mode="before")
    @classmethod
    def _normalize_source_url(cls, value: object) -> object:
        if not isinstance(value, str):
            return value

        normalized = value.strip()
        if not normalized:
            return None

        parsed = urlparse(normalized)
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
            raise ValueError("source_url must be a valid http or https URL")

        return normalized

    @model_validator(mode="after")
    def _require_useful_intake(self) -> JobCreate:
        if any([self.title, self.source_url, self.raw_text]):
            return self
        raise ValueError("job intake requires at least a title, source_url, or raw_text")


class JobRead(JobCreate):
    id: uuid.UUID
    company_id: uuid.UUID | None = None
    company_source_text: str | None = None
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def _project_company_identity(cls, value: object) -> object:
        if isinstance(value, dict):
            data = dict(value)
            data.setdefault("company_source_text", data.get("company"))
            return data

        company_source_text = getattr(value, "company_source_text", None)
        if company_source_text is None:
            company_source_text = getattr(value, "company", None)
        company_identity = getattr(value, "company_identity", None)
        company_name = getattr(company_identity, "name", None) or company_source_text
        return {
            "id": getattr(value, "id", None),
            "source_url": getattr(value, "source_url", None),
            "raw_text": getattr(value, "raw_text", None),
            "title": getattr(value, "title", None),
            "company": company_name,
            "company_id": getattr(value, "company_id", None),
            "company_source_text": company_source_text,
            "location": getattr(value, "location", None),
            "remote_ok": getattr(value, "remote_ok", False),
            "job_type": getattr(value, "job_type", None),
            "ats_type": getattr(value, "ats_type", None),
            "salary_raw": getattr(value, "salary_raw", None),
            "created_at": getattr(value, "created_at", None),
            "updated_at": getattr(value, "updated_at", None),
        }

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Application schemas
# ---------------------------------------------------------------------------

class ApplicationCreate(BaseModel):
    job_id: uuid.UUID
    automation_mode: str = "manual"


class ApplicationRead(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    job: JobRead | None = None
    state: ApplicationState
    automation_mode: str
    fit_score: int | None = None
    confidence: str | None = None
    recommendation: str | None = None
    score_reasons: list | None = None
    score_risks: list | None = None
    missing_data: list | None = None
    red_flags: list | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApplicationStateUpdate(BaseModel):
    state: ApplicationState
    actor: str = "system"
    payload: dict | None = None


class ApplicationScoreRequest(BaseModel):
    actor: str = "scoring"


# ---------------------------------------------------------------------------
# Application packet review schemas
# ---------------------------------------------------------------------------

class ApplicationPacketReviewCreate(BaseModel):
    decision: str = Field(pattern="^(approved|rejected|changes_requested)$")
    reviewed_by: str = Field(min_length=1, max_length=64)
    source: str = Field(default="dashboard", pattern="^dashboard$")
    packet_text: str | None = None
    notes: str | None = None

    @field_validator("reviewed_by", mode="before")
    @classmethod
    def _normalize_reviewed_by(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        normalized = value.strip()
        if not normalized:
            raise ValueError("reviewed_by must not be blank")
        return normalized

    @field_validator("packet_text", "notes", mode="before")
    @classmethod
    def _normalize_packet_review_optional_text(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        normalized = value.replace("\r\n", "\n").replace("\r", "\n").strip()
        return normalized or None


class ApplicationPacketReviewRead(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    decision: str
    reviewed_by: str
    source: str
    packet_text: str | None = None
    notes: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Confidence/explanation schema  (locked architecture sec. 8)
# ---------------------------------------------------------------------------

class ScoringResult(BaseModel):
    fit_score: int = Field(ge=0, le=100)
    confidence: str = Field(pattern="^(high|medium|low)$")
    recommendation: str = Field(pattern="^(recommended|needs_review|not_recommended)$")
    reasons: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Event log schemas
# ---------------------------------------------------------------------------

class EventLogRead(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    event_type: str
    actor: str
    from_state: str | None = None
    to_state: str | None = None
    payload: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApplicationAuditRead(BaseModel):
    application: ApplicationRead
    events: list[EventLogRead]
    policy_decisions: list[PolicyDecisionRead]
    executor_actions: list[ExecutorActionRead]


class ApplicationReviewSummaryRead(BaseModel):
    application: ApplicationRead
    latest_policy_decision: PolicyDecisionRead | None = None
    latest_executor_action: ExecutorActionRead | None = None
    latest_packet_review: ApplicationPacketReviewRead | None = None
    packet_reviews: list[ApplicationPacketReviewRead] = Field(default_factory=list)
    event_count: int
    next_states: list[str]
    ready_for_policy: bool
    ready_for_dry_run: bool
    ready_for_submission: bool


# ---------------------------------------------------------------------------
# M5 document/answer/packet schemas
# ---------------------------------------------------------------------------
# Request models keep semantically validated fields as plain types so the tracker
# can enforce canonical-value, blank, payload, mode, and reference rules and the
# router can map them to 400/404/409. FastAPI's 422 is reserved for syntactically
# malformed JSON/UUID/type input. Content fields (content, content_json,
# question_text, answer_text) are never trimmed or rewritten.


class DocumentCreate(BaseModel):
    doc_type: str
    name: str


class DocumentRead(BaseModel):
    id: uuid.UUID
    doc_type: str
    name: str
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentVersionCreate(BaseModel):
    content: str | None = None
    content_json: dict | None = None


class DocumentVersionRead(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    version_number: int
    content: str | None = None
    content_json: dict | None = None
    checksum: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AnswerCreate(BaseModel):
    question_key: str
    question_text: str
    answer_text: str


class AnswerUpdate(BaseModel):
    question_text: str | None = None
    answer_text: str | None = None


class AnswerRead(BaseModel):
    id: uuid.UUID
    question_key: str
    question_text: str
    answer_text: str
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApplicationDocumentCreate(BaseModel):
    document_version_id: uuid.UUID
    role: str
    display_order: int
    actor: str | None = None


class ApplicationDocumentRead(BaseModel):
    """Attachment projection: own identity plus the linked document/version facts."""

    id: uuid.UUID
    application_id: uuid.UUID
    document_id: uuid.UUID
    document_version_id: uuid.UUID
    role: str
    display_order: int
    version_number: int
    checksum: str
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def _project(cls, value: object) -> object:
        if isinstance(value, dict):
            return value
        version = getattr(value, "document_version", None)
        return {
            "id": getattr(value, "id", None),
            "application_id": getattr(value, "application_id", None),
            "document_id": getattr(version, "document_id", None),
            "document_version_id": getattr(value, "document_version_id", None),
            "role": getattr(value, "role", None),
            "display_order": getattr(value, "display_order", None),
            "version_number": getattr(version, "version_number", None),
            "checksum": getattr(version, "checksum", None),
            "created_at": getattr(value, "created_at", None),
        }

    model_config = {"from_attributes": True}


class ApplicationAnswerCreate(BaseModel):
    answer_library_id: uuid.UUID | None = None
    question_key: str | None = None
    question_text: str | None = None
    answer_text: str | None = None
    actor: str | None = None


class ApplicationAnswerRead(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    answer_library_id: uuid.UUID | None = None
    question_key: str
    question_text: str
    answer_text: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PacketDocumentRead(BaseModel):
    """Deterministic packet projection of one attached, exact document version."""

    application_document_id: uuid.UUID
    document_id: uuid.UUID
    document_version_id: uuid.UUID
    role: str
    version_number: int
    checksum: str
    display_order: int

    @model_validator(mode="before")
    @classmethod
    def _project(cls, value: object) -> object:
        if isinstance(value, dict):
            return value
        version = getattr(value, "document_version", None)
        return {
            "application_document_id": getattr(value, "id", None),
            "document_id": getattr(version, "document_id", None),
            "document_version_id": getattr(value, "document_version_id", None),
            "role": getattr(value, "role", None),
            "version_number": getattr(version, "version_number", None),
            "checksum": getattr(version, "checksum", None),
            "display_order": getattr(value, "display_order", None),
        }

    model_config = {"from_attributes": True}


class PacketAnswerRead(BaseModel):
    """Packet projection of one immutable answer snapshot (never re-derived from the library)."""

    application_answer_id: uuid.UUID
    answer_library_id: uuid.UUID | None = None
    question_key: str
    question_text: str
    answer_text: str

    @model_validator(mode="before")
    @classmethod
    def _project(cls, value: object) -> object:
        if isinstance(value, dict):
            return value
        return {
            "application_answer_id": getattr(value, "id", None),
            "answer_library_id": getattr(value, "answer_library_id", None),
            "question_key": getattr(value, "question_key", None),
            "question_text": getattr(value, "question_text", None),
            "answer_text": getattr(value, "answer_text", None),
        }

    model_config = {"from_attributes": True}


class ApplicationPacketRead(BaseModel):
    application: ApplicationRead
    documents: list[PacketDocumentRead] = Field(default_factory=list)
    answers: list[PacketAnswerRead] = Field(default_factory=list)
    latest_packet_review: ApplicationPacketReviewRead | None = None
