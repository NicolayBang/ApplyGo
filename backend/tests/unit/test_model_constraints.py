"""Tests for architecture-critical ORM constraints."""

from sqlalchemy import CheckConstraint

from applypilot.db.models import (
    Application,
    ApplicationPacketReview,
    Company,
    Document,
    EmailThread,
    EventLogEntry,
    ExecutorAction,
    Job,
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
    assert application_fk_ondelete(ApplicationPacketReview) is None

    assert "delete" not in Application.events.property.cascade
    assert "delete-orphan" not in Application.events.property.cascade
    assert Application.events.property.passive_deletes == "all"

    assert "delete" not in Application.policy_decisions.property.cascade
    assert "delete-orphan" not in Application.policy_decisions.property.cascade
    assert Application.policy_decisions.property.passive_deletes == "all"

    assert "delete" not in Application.executor_actions.property.cascade
    assert "delete-orphan" not in Application.executor_actions.property.cascade
    assert Application.executor_actions.property.passive_deletes == "all"

    assert "delete" not in Application.packet_reviews.property.cascade
    assert "delete-orphan" not in Application.packet_reviews.property.cascade
    assert Application.packet_reviews.property.passive_deletes == "all"


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


def test_application_packet_review_schema_matches_m2_contract() -> None:
    table = ApplicationPacketReview.__table__

    assert table.c.decision.nullable is False
    assert table.c.reviewed_by.nullable is False
    assert table.c.source.nullable is False
    assert table.c.packet_text.nullable is True
    assert table.c.notes.nullable is True

    assert {
        "ck_application_packet_reviews_decision_m2",
        "ck_application_packet_reviews_source_m2",
    }.issubset(check_constraint_names(ApplicationPacketReview))

    assert {
        "ix_application_packet_reviews_application_id",
        "ix_application_packet_reviews_created_at",
    }.issubset({index.name for index in ApplicationPacketReview.__table__.indexes})


def test_company_identity_schema_matches_m3_compatibility_contract() -> None:
    company_table = Company.__table__
    job_table = Job.__table__

    assert company_table.c.name.nullable is False
    assert company_table.c.normalized_name.nullable is False
    assert company_table.c.domain.nullable is True
    assert company_table.c.normalized_domain.nullable is True
    assert job_table.c.company.nullable is True
    assert job_table.c.company_id.nullable is True

    company_fk = next(iter(job_table.c.company_id.foreign_keys))
    assert company_fk.column.table.name == "companies"
    assert company_fk.ondelete is None

    assert {
        "ck_companies_name_not_blank_m3",
        "ck_companies_normalized_name_not_blank_m3",
    }.issubset(check_constraint_names(Company))

    assert {
        "ix_companies_normalized_name",
        "ix_companies_normalized_domain",
        "uq_companies_normalized_domain_m3",
        "uq_companies_normalized_name_without_domain_m3",
    }.issubset({index.name for index in Company.__table__.indexes})
    assert "ix_jobs_company_id" in {index.name for index in Job.__table__.indexes}


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
