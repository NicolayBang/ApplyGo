"""Tests for architecture-critical ORM constraints."""

from applypilot.db.models import (
    Document,
    EmailThread,
    EventLogEntry,
    ExecutorAction,
    PolicyDecision,
)


def application_fk_ondelete(model: type, column_name: str = "application_id") -> str | None:
    column = model.__table__.c[column_name]
    foreign_key = next(iter(column.foreign_keys))
    return foreign_key.ondelete


def test_application_owned_records_cascade_with_application() -> None:
    assert application_fk_ondelete(Document) == "CASCADE"
    assert application_fk_ondelete(EmailThread) == "CASCADE"
    assert application_fk_ondelete(PolicyDecision) == "CASCADE"
    assert application_fk_ondelete(ExecutorAction) == "CASCADE"


def test_event_log_does_not_cascade_delete_with_application() -> None:
    assert application_fk_ondelete(EventLogEntry) is None


def test_executor_idempotency_key_is_unique() -> None:
    assert ExecutorAction.__table__.c.idempotency_key.unique is True


def test_event_log_has_replay_indexes() -> None:
    index_names = {index.name for index in EventLogEntry.__table__.indexes}

    assert "ix_event_log_application_id" in index_names
    assert "ix_event_log_event_type" in index_names
    assert "ix_event_log_created_at" in index_names
