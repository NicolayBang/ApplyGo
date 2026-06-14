"""Unit tests for guarded application submission workflow behavior."""

from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

from applypilot.db.models import EventLogEntry
from applypilot.db.tracker import Tracker
from applypilot.domain.state_machine import InvalidStateTransitionError


class FakeSession:
    def __init__(self, application: object) -> None:
        self.application = application
        self.added = []
        self.flush_count = 0

    def get(self, model, item_id):  # noqa: ANN001
        if item_id == self.application.id:
            return self.application
        return None

    def add(self, item: object) -> None:
        self.added.append(item)

    def flush(self) -> None:
        self.flush_count += 1


def make_tracker(state: str = "Approved") -> Tracker:
    application = SimpleNamespace(
        id=uuid.uuid4(),
        state=state,
        updated_at=None,
    )
    return Tracker(FakeSession(application))


def test_generic_update_state_rejects_direct_submitted_transition() -> None:
    tracker = make_tracker()

    with pytest.raises(InvalidStateTransitionError, match="submit_application workflow"):
        tracker.update_state(
            application_id=tracker._session.application.id,
            new_state="Submitted",
        )


def test_submit_application_requires_allowed_policy_decision() -> None:
    tracker = make_tracker()
    tracker.get_policy_decisions = lambda application_id: []
    tracker.get_executor_actions = lambda application_id: []

    with pytest.raises(InvalidStateTransitionError, match="allowed policy decision"):
        tracker.submit_application(tracker._session.application.id)

    assert tracker._session.application.state == "Approved"


def test_submit_application_requires_matching_executor_evidence() -> None:
    tracker = make_tracker()
    policy_id = uuid.uuid4()
    tracker.get_policy_decisions = lambda application_id: [
        SimpleNamespace(id=policy_id, allowed=True)
    ]
    tracker.get_executor_actions = lambda application_id: []

    with pytest.raises(InvalidStateTransitionError, match="executor evidence"):
        tracker.submit_application(tracker._session.application.id)

    assert tracker._session.application.state == "Approved"


def test_submit_application_records_state_change_with_required_evidence() -> None:
    tracker = make_tracker()
    policy_id = uuid.uuid4()
    tracker.get_policy_decisions = lambda application_id: [
        SimpleNamespace(id=policy_id, allowed=True)
    ]
    tracker.get_executor_actions = lambda application_id: [
        SimpleNamespace(
            payload={"policy_decision_id": str(policy_id)},
            result={"status": "planned"},
        )
    ]

    application = tracker.submit_application(
        tracker._session.application.id,
        actor="user",
        payload={"source": "test"},
    )

    assert application.state == "Submitted"
    assert tracker._session.flush_count == 2
    [event] = [
        item for item in tracker._session.added if isinstance(item, EventLogEntry)
    ]
    assert event.event_type == "application.state_changed"
    assert event.actor == "user"
    assert event.from_state == "Approved"
    assert event.to_state == "Submitted"
    assert event.payload == {"source": "test"}
