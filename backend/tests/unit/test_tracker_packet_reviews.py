"""Unit tests for packet review tracker persistence."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from applypilot.db.models import Application, ApplicationPacketReview, EventLogEntry
from applypilot.db.tracker import Tracker
from applypilot.domain.applications.models import ApplicationPacketReviewCreate


class FakeQuery:
    def __init__(self, rows: list[ApplicationPacketReview]) -> None:
        self.rows = rows
        self.application_id: uuid.UUID | None = None

    def filter(self, expression):  # noqa: ANN001
        self.application_id = expression.right.value
        return self

    def order_by(self, expression):  # noqa: ANN001
        return self

    def all(self) -> list[ApplicationPacketReview]:
        rows = [
            review
            for review in self.rows
            if self.application_id is None or review.application_id == self.application_id
        ]
        return sorted(rows, key=lambda review: review.created_at)


class FakeSession:
    def __init__(self, application: object | None = None) -> None:
        self.application = application
        self.packet_reviews: list[ApplicationPacketReview] = []
        self.added: list[object] = []
        self.flush_count = 0

    def get(self, model, item_id):  # noqa: ANN001
        if model is Application and self.application and item_id == self.application.id:
            return self.application
        return None

    def add(self, item: object) -> None:
        if isinstance(item, ApplicationPacketReview):
            item.id = uuid.uuid4()
            item.created_at = datetime.now(tz=UTC)
            self.packet_reviews.append(item)
        self.added.append(item)

    def flush(self) -> None:
        self.flush_count += 1

    def query(self, model):  # noqa: ANN001
        if model is ApplicationPacketReview:
            return FakeQuery(self.packet_reviews)
        raise AssertionError(f"Unexpected query model: {model}")


def make_application() -> SimpleNamespace:
    return SimpleNamespace(id=uuid.uuid4())


def test_record_packet_review_persists_human_review_and_audit_event() -> None:
    application = make_application()
    session = FakeSession(application)
    tracker = Tracker(session)  # type: ignore[arg-type]

    review = tracker.record_packet_review(
        application.id,
        ApplicationPacketReviewCreate(
            decision="approved",
            reviewed_by=" Nicolay ",
            source="dashboard",
            packet_text=None,
            notes=" Ready for manual use. ",
        ),
    )

    assert review.application_id == application.id
    assert review.decision == "approved"
    assert review.reviewed_by == "Nicolay"
    assert review.source == "dashboard"
    assert review.packet_text is None
    assert review.notes == "Ready for manual use."
    assert session.flush_count == 2
    assert isinstance(session.added[0], ApplicationPacketReview)

    [event] = [item for item in session.added if isinstance(item, EventLogEntry)]
    assert event.application_id == application.id
    assert event.event_type == "application_packet.reviewed"
    assert event.actor == "Nicolay"
    assert event.payload == {
        "packet_review_id": str(review.id),
        "decision": "approved",
        "reviewed_by": "Nicolay",
        "source": "dashboard",
        "notes_present": True,
        "packet_text_persisted": False,
    }
    assert "packet_text" not in event.payload


def test_record_packet_review_rejects_missing_application() -> None:
    tracker = Tracker(FakeSession())  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Application .* not found"):
        tracker.record_packet_review(
            uuid.uuid4(),
            ApplicationPacketReviewCreate(
                decision="approved",
                reviewed_by="human",
            ),
        )


def test_packet_review_request_rejects_unapproved_values() -> None:
    with pytest.raises(ValidationError):
        ApplicationPacketReviewCreate(decision="maybe", reviewed_by="human")

    with pytest.raises(ValidationError):
        ApplicationPacketReviewCreate(
            decision="approved",
            reviewed_by="human",
            source="browser",
        )


def test_get_packet_reviews_returns_application_reviews_oldest_first() -> None:
    application = make_application()
    other_application = make_application()
    now = datetime.now(tz=UTC)
    session = FakeSession(application)
    session.packet_reviews = [
        ApplicationPacketReview(
            id=uuid.uuid4(),
            application_id=application.id,
            decision="rejected",
            reviewed_by="human",
            source="dashboard",
            created_at=now + timedelta(minutes=2),
        ),
        ApplicationPacketReview(
            id=uuid.uuid4(),
            application_id=application.id,
            decision="approved",
            reviewed_by="human",
            source="dashboard",
            created_at=now,
        ),
        ApplicationPacketReview(
            id=uuid.uuid4(),
            application_id=other_application.id,
            decision="approved",
            reviewed_by="human",
            source="dashboard",
            created_at=now - timedelta(minutes=1),
        ),
    ]
    tracker = Tracker(session)  # type: ignore[arg-type]

    reviews = tracker.get_packet_reviews(application.id)

    assert [review.decision for review in reviews] == ["approved", "rejected"]
