"""Placeholder event log contracts."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class EventRecord:
    """Append-only event placeholder."""

    id: str
    application_id: str
    event_type: str
    actor: str
    from_state: str | None
    to_state: str | None
    payload: dict[str, Any]
    created_at: datetime
