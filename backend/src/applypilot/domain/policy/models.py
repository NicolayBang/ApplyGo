"""Policy request and decision models."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class AutomationMode(StrEnum):
    MANUAL = "manual"
    SEMI_AUTO = "semi_auto"
    FULL_AUTO = "full_auto"
    DRY_RUN = "dry_run"


class ConfidenceLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PolicyDecisionOutcome(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    REVIEW = "review"


class WorkerType(StrEnum):
    EMAIL = "email"
    BROWSER = "browser"
    DOCUMENTS = "documents"


@dataclass(slots=True)
class PolicyContext:
    """Risk and confidence inputs used by policy evaluation."""

    confidence: ConfidenceLevel
    fit_score: int | None = None
    recommendation: str | None = None
    reasons: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    missing_data: list[str] = field(default_factory=list)
    red_flags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class PolicyRequest:
    """Structured action request presented to the policy gate."""

    application_id: UUID
    current_state: str
    requested_action: str
    worker: WorkerType
    context: PolicyContext
    mode: AutomationMode


@dataclass(slots=True)
class PolicyDecision:
    """Policy decision returned before any executor invocation."""

    decision: PolicyDecisionOutcome
    mode: AutomationMode
    reasons: list[str] = field(default_factory=list)
    required_overrides: list[str] = field(default_factory=list)
    decision_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))

    @property
    def allowed(self) -> bool:
        """Compatibility helper for storage layers that persist boolean permission."""
        return self.decision == PolicyDecisionOutcome.ALLOW
