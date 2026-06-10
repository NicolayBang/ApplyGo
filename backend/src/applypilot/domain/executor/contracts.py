"""Shared executor request and result contracts."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ExecutionMode(StrEnum):
    EXECUTE = "execute"
    DRY_RUN = "dry_run"


@dataclass(slots=True)
class ExecutorRequest:
    """Worker command placeholder with idempotency and audit metadata."""

    action_type: str
    mode: ExecutionMode
    application_id: str
    idempotency_key: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ExecutorResult:
    """Worker result placeholder returned from execute or dry-run."""

    status: str
    details: dict[str, Any] = field(default_factory=dict)
