"""Pydantic schemas for policy API boundaries."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from applypilot.domain.policy.models import (
    AutomationMode,
    ConfidenceLevel,
    PolicyDecisionOutcome,
    WorkerType,
)


class PolicyContextInput(BaseModel):
    confidence: ConfidenceLevel
    fit_score: int | None = Field(default=None, ge=0, le=100)
    recommendation: str | None = Field(
        default=None,
        pattern="^(recommended|needs_review|not_recommended)$",
    )
    reasons: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)


class PolicyEvaluationRequest(BaseModel):
    requested_action: str
    worker: WorkerType
    context: PolicyContextInput | None = None
    mode: AutomationMode | None = None
    actor: str = "policy"


class PolicyDecisionRead(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    action_type: str
    mode: AutomationMode
    decision: PolicyDecisionOutcome
    allowed: bool
    reasons: list | None = None
    risks: list | None = None
    required_overrides: list | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
