"""Pydantic schemas for executor API boundaries."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from applypilot.domain.executor.contracts import ExecutionMode


class ExecutorDryRunRequest(BaseModel):
    policy_decision_id: uuid.UUID
    action_type: str
    idempotency_key: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    actor: str = "worker"


class ExecutorActionRead(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    idempotency_key: str
    action_type: str
    execution_mode: ExecutionMode
    status: str
    payload: dict | None = None
    result: dict | None = None
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}
