"""Domain schemas for the canonical application record.

These Pydantic models are used at the API layer.
SQLAlchemy ORM models live in applypilot.db.models.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


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
    state: str
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
    state: str
    actor: str = "system"
    payload: dict | None = None


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
