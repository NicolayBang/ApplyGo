"""Tracker-level coverage for the M5 document/answer/packet read-model (PR3, Issue #219).

These tests exercise the ``Tracker`` M5 methods directly against PostgreSQL inside a
single rolled-back transaction (no commit), so no data persists. They are skipped
automatically when the database is unreachable, following the established
``test_seed_to_dashboard.py`` pattern.

Covered: canonical type/role validation, blank-field rejection, actor default/blank
normalization, partial answer patch behavior, per-document next-version allocation and
deterministic checksums, exact-version attachment semantics, source-copy and manual
snapshot behavior, duplicate-conflict handling, and metadata-only audit payloads.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from applypilot.config.settings import get_settings
from applypilot.db.tracker import (
    M5ConflictError,
    M5NotFoundError,
    M5ValidationError,
    Tracker,
    _content_checksum,
)
from applypilot.domain.applications.models import ApplicationCreate, JobCreate

_CONNECT_TIMEOUT = 2
_FORBIDDEN_AUDIT_KEYS = {"content", "content_json", "question_text", "answer_text"}


@pytest.fixture()
def db_session():
    """Connect to PostgreSQL and yield a rolled-back session (skip if unreachable)."""
    settings = get_settings()
    engine = create_engine(
        settings.database_url,
        future=True,
        connect_args={"connect_timeout": _CONNECT_TIMEOUT},
    )
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        engine.dispose()
        pytest.skip(f"PostgreSQL not available (start with: docker compose up -d postgres): {exc}")

    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        engine.dispose()


def _make_application(tracker: Tracker):
    job = tracker.create_job(JobCreate(title="Backend Engineer", company="ApplyPilot"))
    return tracker.create_application(ApplicationCreate(job_id=job.id))


def _event_payloads(tracker: Tracker, application_id, event_type: str) -> list[dict]:
    return [e.payload for e in tracker.get_events(application_id) if e.event_type == event_type]


# ---------------------------------------------------------------------------
# Document + version validation and allocation
# ---------------------------------------------------------------------------

def test_create_document_rejects_non_canonical_type_and_blank_name(db_session) -> None:
    tracker = Tracker(db_session)

    with pytest.raises(M5ValidationError):
        tracker.create_document(doc_type="banana", name="My doc")
    with pytest.raises(M5ValidationError):
        tracker.create_document(doc_type="resume", name="   ")


def test_create_document_trims_name(db_session) -> None:
    tracker = Tracker(db_session)

    document = tracker.create_document(doc_type="resume", name="  Primary resume  ")

    assert document.name == "Primary resume"
    assert document.doc_type == "resume"
    assert document.is_archived is False


def test_add_version_requires_payload_and_allocates_per_document_numbers(db_session) -> None:
    tracker = Tracker(db_session)
    document = tracker.create_document(doc_type="resume", name="Resume")

    with pytest.raises(M5ValidationError):
        tracker.add_document_version(document.id)

    first = tracker.add_document_version(document.id, content="  body one  ")
    second = tracker.add_document_version(document.id, content_json={"b": 2, "a": 1})

    assert (first.version_number, second.version_number) == (1, 2)
    # Content is stored verbatim (no trimming/rewriting of payload).
    assert first.content == "  body one  "
    assert first.checksum == _content_checksum("  body one  ", None)
    assert second.checksum == _content_checksum(None, {"b": 2, "a": 1})


def test_add_version_to_missing_document_raises_not_found(db_session) -> None:
    tracker = Tracker(db_session)

    with pytest.raises(M5NotFoundError):
        tracker.add_document_version(uuid.uuid4(), content="x")


def test_archived_document_may_still_receive_versions(db_session) -> None:
    tracker = Tracker(db_session)
    document = tracker.create_document(doc_type="other", name="Archived doc")
    tracker.add_document_version(document.id, content="v1")
    tracker.archive_document(document.id)

    later = tracker.add_document_version(document.id, content="v2")

    assert later.version_number == 2


# ---------------------------------------------------------------------------
# Answer library: create / patch / archive
# ---------------------------------------------------------------------------

def test_create_answer_rejects_blank_key_and_duplicate_active_key(db_session) -> None:
    tracker = Tracker(db_session)

    with pytest.raises(M5ValidationError):
        tracker.create_answer(question_key="   ", question_text="Q", answer_text="A")

    tracker.create_answer(question_key="visa", question_text="Q", answer_text="A")
    with pytest.raises(M5ConflictError):
        tracker.create_answer(question_key="visa", question_text="Q2", answer_text="A2")


def test_partial_answer_patch_updates_only_supplied_fields(db_session) -> None:
    tracker = Tracker(db_session)
    answer = tracker.create_answer(
        question_key="relocation", question_text="Relocate?", answer_text="Yes"
    )

    with pytest.raises(M5ValidationError):
        tracker.update_answer(answer.id)

    updated = tracker.update_answer(answer.id, answer_text="Yes, anywhere")

    assert updated.answer_text == "Yes, anywhere"
    assert updated.question_text == "Relocate?"  # untouched
    assert updated.question_key == "relocation"  # never mutated


def test_archive_answer_is_idempotent_and_frees_active_key(db_session) -> None:
    tracker = Tracker(db_session)
    first = tracker.create_answer(question_key="notice", question_text="Q", answer_text="A")

    tracker.archive_answer(first.id)
    again = tracker.archive_answer(first.id)
    assert again.is_archived is True

    # Archiving freed the active key for a new active answer.
    reused = tracker.create_answer(question_key="notice", question_text="Q2", answer_text="A2")
    assert reused.id != first.id


# ---------------------------------------------------------------------------
# Attachments: exact version, role/order validation, actor, duplicates, audit
# ---------------------------------------------------------------------------

def test_attach_validates_role_order_and_binds_exact_version(db_session) -> None:
    tracker = Tracker(db_session)
    application = _make_application(tracker)
    document = tracker.create_document(doc_type="resume", name="Resume")
    v1 = tracker.add_document_version(document.id, content="one")
    v2 = tracker.add_document_version(document.id, content="two")

    with pytest.raises(M5ValidationError):
        tracker.attach_document(
            application.id, document_version_id=v1.id, role="banana", display_order=0
        )
    with pytest.raises(M5ValidationError):
        tracker.attach_document(
            application.id, document_version_id=v1.id, role="resume", display_order=-1
        )

    older = tracker.attach_document(
        application.id, document_version_id=v1.id, role="resume", display_order=0
    )
    newer = tracker.attach_document(
        application.id, document_version_id=v2.id, role="resume", display_order=1
    )

    # Attaching a newer version is a new row; the prior attachment is unchanged.
    assert older.document_version_id == v1.id
    assert newer.document_version_id == v2.id
    assert older.id != newer.id


def test_attach_missing_application_vs_missing_version(db_session) -> None:
    tracker = Tracker(db_session)
    application = _make_application(tracker)

    with pytest.raises(M5NotFoundError):
        tracker.attach_document(
            uuid.uuid4(), document_version_id=uuid.uuid4(), role="resume", display_order=0
        )
    with pytest.raises(M5ValidationError):
        tracker.attach_document(
            application.id, document_version_id=uuid.uuid4(), role="resume", display_order=0
        )


def test_duplicate_exact_attachment_conflicts(db_session) -> None:
    tracker = Tracker(db_session)
    application = _make_application(tracker)
    document = tracker.create_document(doc_type="resume", name="Resume")
    v1 = tracker.add_document_version(document.id, content="one")

    tracker.attach_document(
        application.id, document_version_id=v1.id, role="resume", display_order=0
    )
    with pytest.raises(M5ConflictError):
        tracker.attach_document(
            application.id, document_version_id=v1.id, role="resume", display_order=2
        )


def test_attach_actor_defaults_and_normalizes_in_audit_payload(db_session) -> None:
    tracker = Tracker(db_session)
    application = _make_application(tracker)
    document = tracker.create_document(doc_type="resume", name="Resume")
    v1 = tracker.add_document_version(document.id, content="one")
    v2 = tracker.add_document_version(document.id, content="two")

    tracker.attach_document(
        application.id, document_version_id=v1.id, role="resume", display_order=0, actor=None
    )
    tracker.attach_document(
        application.id,
        document_version_id=v2.id,
        role="resume",
        display_order=1,
        actor="  alex  ",
    )

    payloads = _event_payloads(tracker, application.id, "application_document.attached")
    assert [p["actor"] for p in payloads] == ["system", "alex"]
    # Audit payloads carry identifiers/metadata only, never content.
    for payload in payloads:
        assert _FORBIDDEN_AUDIT_KEYS.isdisjoint(payload.keys())
        assert "version_number" in payload and "document_version_id" in payload


# ---------------------------------------------------------------------------
# Answer snapshots: source-copy, manual, mode rejection, duplicate, immutability
# ---------------------------------------------------------------------------

def test_source_copy_snapshot_copies_library_and_is_immutable(db_session) -> None:
    tracker = Tracker(db_session)
    application = _make_application(tracker)
    answer = tracker.create_answer(
        question_key="why_us", question_text="Why us?", answer_text="Original"
    )

    snapshot = tracker.record_application_answer(application.id, answer_library_id=answer.id)
    assert snapshot.question_key == "why_us"
    assert snapshot.answer_text == "Original"
    assert snapshot.answer_library_id == answer.id

    # Editing then archiving the library answer never mutates the snapshot.
    tracker.update_answer(answer.id, answer_text="Rewritten")
    tracker.archive_answer(answer.id)
    db_session.refresh(snapshot)
    assert snapshot.answer_text == "Original"


def test_archived_library_answer_may_still_seed_snapshot_by_id(db_session) -> None:
    tracker = Tracker(db_session)
    application = _make_application(tracker)
    answer = tracker.create_answer(
        question_key="sponsorship", question_text="Sponsor?", answer_text="No"
    )
    tracker.archive_answer(answer.id)

    snapshot = tracker.record_application_answer(application.id, answer_library_id=answer.id)
    assert snapshot.question_key == "sponsorship"
    assert snapshot.answer_text == "No"


def test_manual_snapshot_and_mode_rejection(db_session) -> None:
    tracker = Tracker(db_session)
    application = _make_application(tracker)

    manual = tracker.record_application_answer(
        application.id,
        question_key="  start_date  ",
        question_text="Start date?",
        answer_text="Immediately",
    )
    assert manual.question_key == "start_date"
    assert manual.answer_library_id is None

    # Incomplete manual mode is rejected.
    with pytest.raises(M5ValidationError):
        tracker.record_application_answer(application.id, question_key="x")

    # Mixed mode (library id plus manual fields) is rejected.
    answer = tracker.create_answer(question_key="k", question_text="Q", answer_text="A")
    with pytest.raises(M5ValidationError):
        tracker.record_application_answer(
            application.id, answer_library_id=answer.id, answer_text="A"
        )


def test_duplicate_application_answer_key_conflicts(db_session) -> None:
    tracker = Tracker(db_session)
    application = _make_application(tracker)
    tracker.record_application_answer(
        application.id, question_key="dup", question_text="Q", answer_text="A"
    )

    with pytest.raises(M5ConflictError):
        tracker.record_application_answer(
            application.id, question_key="dup", question_text="Q2", answer_text="A2"
        )


def test_record_answer_audit_payload_is_metadata_only(db_session) -> None:
    tracker = Tracker(db_session)
    application = _make_application(tracker)
    answer = tracker.create_answer(question_key="meta", question_text="Q", answer_text="Secret")
    tracker.record_application_answer(application.id, answer_library_id=answer.id)

    payloads = _event_payloads(tracker, application.id, "application_answer.recorded")
    assert len(payloads) == 1
    payload = payloads[0]
    assert _FORBIDDEN_AUDIT_KEYS.isdisjoint(payload.keys())
    assert payload["question_key"] == "meta"
    assert payload["answer_library_id"] == str(answer.id)
