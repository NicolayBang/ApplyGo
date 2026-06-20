"""Tests for architecture-critical ORM constraints."""

from sqlalchemy import CheckConstraint

from applypilot.db.models import (
    AnswerLibrary,
    Application,
    ApplicationAnswer,
    ApplicationDocument,
    ApplicationPacketReview,
    Company,
    Document,
    DocumentVersion,
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


def fk_ondelete(model: type, column_name: str) -> str | None:
    column = model.__table__.c[column_name]
    foreign_key = next(iter(column.foreign_keys))
    return foreign_key.ondelete


def index_names(model: type) -> set[str]:
    return {index.name for index in model.__table__.indexes}


def index_by_name(model: type, name: str):
    return next(index for index in model.__table__.indexes if index.name == name)


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
    assert job_table.c.company_source_text.nullable is True
    assert job_table.c.company_id.nullable is False

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
    assert {
        "ix_jobs_company_id",
        "ix_jobs_company_source_text",
    }.issubset({index.name for index in Job.__table__.indexes})


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


# ---------------------------------------------------------------------------
# M5 document / answer model (Proposed contract -> additive implementation)
# ---------------------------------------------------------------------------

def test_m5_documents_logical_library_schema() -> None:
    table = Document.__table__

    # M5 logical-library fields.
    assert table.c.name.nullable is False
    assert table.c.is_archived.nullable is False
    assert table.c.updated_at.nullable is False

    # Legacy single-application columns retained during the compatibility window.
    assert {"application_id", "content", "content_json", "version"}.issubset(table.c.keys())
    assert application_fk_ondelete(Document) == "CASCADE"

    assert {
        "ck_documents_doc_type_m5",
        "ck_documents_name_not_blank_m5",
    }.issubset(check_constraint_names(Document))
    assert {
        "ix_documents_doc_type",
        "ix_documents_is_archived",
    }.issubset(index_names(Document))


def test_m5_document_versions_are_immutable_and_versioned() -> None:
    table = DocumentVersion.__table__

    # Immutable rows carry no updated_at.
    assert "updated_at" not in table.c.keys()
    assert table.c.checksum.nullable is False
    assert fk_ondelete(DocumentVersion, "document_id") == "RESTRICT"

    assert {
        "ck_document_versions_version_positive_m5",
        "ck_document_versions_payload_present_m5",
    }.issubset(check_constraint_names(DocumentVersion))
    assert {
        "ix_document_versions_document_id",
        "ix_document_versions_checksum",
        "uq_document_versions_document_id_version_number_m5",
    }.issubset(index_names(DocumentVersion))
    assert index_by_name(
        DocumentVersion, "uq_document_versions_document_id_version_number_m5"
    ).unique is True


def test_m5_application_documents_bind_exact_version() -> None:
    assert fk_ondelete(ApplicationDocument, "application_id") == "RESTRICT"
    assert fk_ondelete(ApplicationDocument, "document_version_id") == "RESTRICT"

    assert {
        "ck_application_documents_role_m5",
        "ck_application_documents_display_order_non_negative_m5",
    }.issubset(check_constraint_names(ApplicationDocument))
    assert index_by_name(
        ApplicationDocument, "uq_application_documents_app_version_role_m5"
    ).unique is True

    # Append-only, audit-preserving: never delete-cascaded with the application.
    assert "delete" not in Application.application_documents.property.cascade
    assert "delete-orphan" not in Application.application_documents.property.cascade
    assert Application.application_documents.property.passive_deletes == "all"


def test_m5_answer_library_active_uniqueness_and_archive() -> None:
    table = AnswerLibrary.__table__

    assert table.c.is_archived.nullable is False
    assert "ck_answer_library_question_key_not_blank_m5" in check_constraint_names(
        AnswerLibrary
    )

    active_unique = index_by_name(
        AnswerLibrary, "uq_answer_library_question_key_active_m5"
    )
    assert active_unique.unique is True
    # Partial unique index over non-archived rows only.
    assert active_unique.dialect_options["postgresql"]["where"] is not None


def test_m5_application_answers_are_immutable_snapshots() -> None:
    table = ApplicationAnswer.__table__

    # Immutable snapshot: no updated_at; optional library provenance.
    assert "updated_at" not in table.c.keys()
    assert table.c.answer_library_id.nullable is True

    assert fk_ondelete(ApplicationAnswer, "application_id") == "RESTRICT"
    assert fk_ondelete(ApplicationAnswer, "answer_library_id") == "RESTRICT"

    assert "ck_application_answers_question_key_not_blank_m5" in check_constraint_names(
        ApplicationAnswer
    )
    assert index_by_name(
        ApplicationAnswer, "uq_application_answers_app_question_key_m5"
    ).unique is True

    assert "delete" not in Application.application_answers.property.cascade
    assert "delete-orphan" not in Application.application_answers.property.cascade
    assert Application.application_answers.property.passive_deletes == "all"
