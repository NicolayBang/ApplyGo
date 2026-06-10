"""Placeholder event log contracts."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class EventRecord:
    """Append-only event placeholder."""

    event_id: str
    application_id: str
    event_type: str
    actor: str
    payload: dict[str, Any]
    created_at: datetime
