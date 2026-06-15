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
    created_at: datetime
    updated_at: datetime

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

    @field_validator("reviewed_by", "packet_text", "notes", mode="before")
    @classmethod
    def _normalize_optional_text(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        normalized = value.strip()
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
    event_count: int
    next_states: list[str]
    ready_for_policy: bool
    ready_for_dry_run: bool
    ready_for_submission: bool
