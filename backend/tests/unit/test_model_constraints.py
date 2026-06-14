"""Tests for architecture-critical ORM constraints."""

from sqlalchemy import CheckConstraint

from applypilot.db.models import (
    Application,
    Document,
    EmailThread,
    EventLogEntry,
    ExecutorAction,
    PolicyDecision,
)
from applypilot.domain.state_machine import ApplicationState


def application_fk_ondelete(model: type, column_name: str = "application_id") -> str | None:
    column = model.__table__.c[column_name]
    foreign_key = next(iter(column.foreign_keys))
    return foreign_key.ondelete


def check_constraint_names(model: type) -> set[str]:
    return {
        constraint.name
        for constraint in model.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }


def test_application_owned_records_cascade_with_application() -> None:
    assert application_fk_ondelete(Document) == "CASCADE"
    assert application_fk_ondelete(EmailThread) == "CASCADE"


def test_audit_records_do_not_cascade_delete_with_application() -> None:
    assert application_fk_ondelete(EventLogEntry) is None
    assert application_fk_ondelete(PolicyDecision) is None
    assert application_fk_ondelete(ExecutorAction) is None

    assert "delete" not in Application.events.property.cascade
    assert "delete-orphan" not in Application.events.property.cascade
    assert Application.events.property.passive_deletes == "all"

    assert "delete" not in Application.policy_decisions.property.cascade
    assert "delete-orphan" not in Application.policy_decisions.property.cascade
    assert Application.policy_decisions.property.passive_deletes == "all"

    assert "delete" not in Application.executor_actions.property.cascade
    assert "delete-orphan" not in Application.executor_actions.property.cascade
    assert Application.executor_actions.property.passive_deletes == "all"


def test_application_state_default_matches_state_machine() -> None:
    column = Application.__table__.c.state

    assert column.default.arg == ApplicationState.APPLICATION_CREATED.value
    assert column.server_default.arg == ApplicationState.APPLICATION_CREATED.value


def test_executor_idempotency_key_is_unique() -> None:
    assert ExecutorAction.__table__.c.idempotency_key.unique is True


def test_executor_contract_metadata_is_persisted() -> None:
    table = ExecutorAction.__table__.c

    assert table.request_id.unique is True
    assert table.request_id.nullable is False
    assert table.worker.nullable is False
    assert table.requested_by.nullable is False
    assert table.requested_at.nullable is False


def test_event_log_has_replay_indexes() -> None:
    index_names = {index.name for index in EventLogEntry.__table__.indexes}

    assert "ix_event_log_application_id" in index_names
    assert "ix_event_log_event_type" in index_names
    assert "ix_event_log_created_at" in index_names
    assert "ix_executor_actions_request_id" in {
        index.name for index in ExecutorAction.__table__.indexes
    }


def test_m1_value_check_constraints_are_declared_on_models() -> None:
    assert {
        "ck_applications_state_m1",
        "ck_applications_automation_mode_m1",
    }.issubset(check_constraint_names(Application))
    assert {"ck_email_threads_direction_m1"}.issubset(
        check_constraint_names(EmailThread)
    )
    assert {
        "ck_policy_decisions_mode_m1",
        "ck_policy_decisions_decision_m1",
    }.issubset(check_constraint_names(PolicyDecision))
    assert {
        "ck_executor_actions_execution_mode_m1",
        "ck_executor_actions_status_m1",
        "ck_executor_actions_worker_m1",
    }.issubset(check_constraint_names(ExecutorAction))
