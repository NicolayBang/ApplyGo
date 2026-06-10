"""Policy modes and decision placeholders."""

from dataclasses import dataclass, field
from enum import StrEnum


class AutomationMode(StrEnum):
    MANUAL = "manual"
    SEMI_AUTO = "semi_auto"
    FULL_AUTO = "full_auto"
    DRY_RUN = "dry_run"


@dataclass(slots=True)
class PolicyDecision:
    """Structured decision placeholder for policy evaluation."""

    allowed: bool
    mode: AutomationMode
    reasons: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
