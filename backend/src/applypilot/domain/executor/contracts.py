"""Shared executor request and result contracts."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class ExecutionMode(StrEnum):
    EXECUTE = "execute"
    DRY_RUN = "dry_run"


@dataclass(slots=True)
class ExecutorRequest:
    """Worker command placeholder with idempotency and audit metadata."""

    request_id: UUID
    action_type: str
    mode: ExecutionMode
    application_id: str
    worker: str
    idempotency_key: str
    requested_by: str = "system"
    requested_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))
    payload: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        action_type: str,
        mode: ExecutionMode,
        application_id: str,
        worker: str,
        idempotency_key: str,
        requested_by: str = "system",
        payload: dict[str, Any] | None = None,
    ) -> "ExecutorRequest":
        """Create an executor request with contract metadata generated at the boundary."""
        return cls(
            request_id=uuid4(),
            action_type=action_type,
            mode=mode,
            application_id=application_id,
            worker=worker,
            idempotency_key=idempotency_key,
            requested_by=requested_by,
            payload=payload or {},
        )


@dataclass(slots=True)
class ExecutorResult:
    """Worker result placeholder returned from execute or dry-run."""

    request_id: UUID
    application_id: str
    worker: str
    mode: ExecutionMode
    status: str
    details: dict[str, Any] = field(default_factory=dict)
    error_code: str | None = None
    error_message: str | None = None
    completed_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))
