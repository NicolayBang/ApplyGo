"""Regression coverage for the M5 document/answer schema migration (0012).

Exercises the deterministic legacy-document backfill, idempotent re-run behavior,
``ON DELETE RESTRICT`` retention, and contract-invalid write rejection against a
real PostgreSQL server. Each test runs inside a throwaway schema and is skipped
automatically at runtime when the database is unreachable.

The schema here is hand-built (mirroring migration ``0012``) so the backfill
function can be exercised in isolation, following the established pattern in
``test_company_cutover_migration.py``. The full ``alembic upgrade head`` path is
validated separately by the migration/quality-gate suite.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from applypilot.config.settings import get_settings

_CONNECT_TIMEOUT = 2

_DOC_TYPE_CHECK = (
    "doc_type IN ('resume', 'cover_letter', 'supporting', 'other')"
)
_ROLE_CHECK = "role IN ('resume', 'cover_letter', 'supporting', 'other')"


@pytest.fixture()
def db_session():
    """Connect to PostgreSQL and yield a transactional session (skip if unreachable)."""
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


def _expected_checksum(content: str | None, content_json: object) -> str:
    """Independent re-implementation of the documented checksum algorithm."""
    envelope = {"content": content, "content_json": content_json}
    canonical = json.dumps(
        envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _isolate_schema(session) -> None:
    schema_name = f"m5_migration_regression_{uuid.uuid4().hex}"
    session.execute(text(f'CREATE SCHEMA "{schema_name}"'))
    session.execute(text(f'SET LOCAL search_path TO "{schema_name}"'))


def _create_m5_tables(session, *, with_doc_type_check: bool) -> None:
    """Create the legacy + M5 tables in the active schema, mirroring migration 0012."""
    session.execute(
        text(
            """
            CREATE TABLE applications (
                id uuid PRIMARY KEY,
                created_at timestamptz NOT NULL DEFAULT now()
            )
            """
        )
    )
    doc_type_clause = (
        f", CONSTRAINT ck_documents_doc_type_m5 CHECK ({_DOC_TYPE_CHECK})"
        if with_doc_type_check
        else ""
    )
    session.execute(
        text(
            f"""
            CREATE TABLE documents (
                id uuid PRIMARY KEY,
                application_id uuid NOT NULL
                    REFERENCES applications(id) ON DELETE CASCADE,
                doc_type varchar(64) NOT NULL,
                content text,
                content_json jsonb,
                version integer NOT NULL DEFAULT 1,
                name varchar(256),
                is_archived boolean NOT NULL DEFAULT false,
                created_at timestamptz NOT NULL DEFAULT now(),
                updated_at timestamptz NOT NULL DEFAULT now(),
                CONSTRAINT ck_documents_name_not_blank_m5 CHECK (name <> ''){doc_type_clause}
            )
            """
        )
    )
    session.execute(
        text(
            """
            CREATE TABLE document_versions (
                id uuid PRIMARY KEY,
                document_id uuid NOT NULL
                    REFERENCES documents(id) ON DELETE RESTRICT,
                version_number integer NOT NULL,
                content text,
                content_json jsonb,
                checksum varchar(128) NOT NULL,
                created_at timestamptz NOT NULL DEFAULT now(),
                CONSTRAINT ck_document_versions_version_positive_m5
                    CHECK (version_number > 0),
                CONSTRAINT ck_document_versions_payload_present_m5
                    CHECK (content IS NOT NULL OR content_json IS NOT NULL),
                CONSTRAINT uq_document_versions_document_id_version_number_m5
                    UNIQUE (document_id, version_number)
            )
            """
        )
    )
    session.execute(
        text(
            f"""
            CREATE TABLE application_documents (
                id uuid PRIMARY KEY,
                application_id uuid NOT NULL
                    REFERENCES applications(id) ON DELETE RESTRICT,
                document_version_id uuid NOT NULL
                    REFERENCES document_versions(id) ON DELETE RESTRICT,
                role varchar(64) NOT NULL,
                display_order integer NOT NULL,
                created_at timestamptz NOT NULL DEFAULT now(),
                CONSTRAINT ck_application_documents_role_m5 CHECK ({_ROLE_CHECK}),
                CONSTRAINT ck_application_documents_display_order_non_negative_m5
                    CHECK (display_order >= 0),
                CONSTRAINT uq_application_documents_app_version_role_m5
                    UNIQUE (application_id, document_version_id, role)
            )
            """
        )
    )
    session.execute(
        text(
            """
            CREATE TABLE answer_library (
                id uuid PRIMARY KEY,
                question_key varchar(256) NOT NULL,
                question_text text NOT NULL,
                answer_text text NOT NULL,
                is_archived boolean NOT NULL DEFAULT false,
                created_at timestamptz NOT NULL DEFAULT now(),
                updated_at timestamptz NOT NULL DEFAULT now(),
                CONSTRAINT ck_answer_library_question_key_not_blank_m5
                    CHECK (question_key <> '')
            )
            """
        )
    )
    session.execute(
        text(
            """
            CREATE UNIQUE INDEX uq_answer_library_question_key_active_m5
            ON answer_library (question_key) WHERE is_archived IS false
            """
        )
    )
    session.execute(
        text(
            """
            CREATE TABLE application_answers (
                id uuid PRIMARY KEY,
                application_id uuid NOT NULL
                    REFERENCES applications(id) ON DELETE RESTRICT,
                answer_library_id uuid
                    REFERENCES answer_library(id) ON DELETE RESTRICT,
                question_key varchar(256) NOT NULL,
                question_text text NOT NULL,
                answer_text text NOT NULL,
                created_at timestamptz NOT NULL DEFAULT now(),
                CONSTRAINT ck_application_answers_question_key_not_blank_m5
                    CHECK (question_key <> ''),
                CONSTRAINT uq_application_answers_app_question_key_m5
                    UNIQUE (application_id, question_key)
            )
            """
        )
    )


# Representative legacy `documents` rows covering aliases, unknown/blank types,
# null/text/json payloads, and positive/invalid versions.
def _representative_legacy_rows() -> list[dict]:
    return [
        {
            "key": "resume_alias_text",
            "doc_type": "CV",
            "content": "resume text",
            "content_json": None,
            "version": 1,
            "expected_type": "resume",
            "expected_name": "Legacy resume",
            "expected_version": 1,
            "expected_content": "resume text",
            "expected_json": None,
            "created_at": "2026-06-10 09:00:00+00",
        },
        {
            "key": "cover_letter_alias_json",
            "doc_type": "Cover Letter",
            "content": None,
            "content_json": {"greeting": "Hi", "body": "Please consider me."},
            "version": 2,
            "expected_type": "cover_letter",
            "expected_name": "Legacy cover letter",
            "expected_version": 2,
            "expected_content": None,
            "expected_json": {"greeting": "Hi", "body": "Please consider me."},
            "created_at": "2026-06-10 09:01:00+00",
        },
        {
            "key": "unknown_type_both_payloads",
            "doc_type": "random_type",
            "content": "misc content",
            "content_json": {"k": 1},
            "version": 1,
            "expected_type": "other",
            "expected_name": "Legacy other document",
            "expected_version": 1,
            "expected_content": "misc content",
            "expected_json": {"k": 1},
            "created_at": "2026-06-10 09:02:00+00",
        },
        {
            "key": "blank_type_null_payloads",
            "doc_type": "",
            "content": None,
            "content_json": None,
            "version": 1,
            "expected_type": "other",
            "expected_name": "Legacy other document",
            "expected_version": 1,
            "expected_content": "",
            "expected_json": None,
            "created_at": "2026-06-10 09:03:00+00",
        },
        {
            "key": "supporting_positive_version",
            "doc_type": "supporting",
            "content": "reference letter",
            "content_json": None,
            "version": 3,
            "expected_type": "supporting",
            "expected_name": "Legacy supporting document",
            "expected_version": 3,
            "expected_content": "reference letter",
            "expected_json": None,
            "created_at": "2026-06-10 09:04:00+00",
        },
        {
            "key": "other_invalid_version",
            "doc_type": "other",
            "content": "fallback",
            "content_json": None,
            "version": 0,
            "expected_type": "other",
            "expected_name": "Legacy other document",
            "expected_version": 1,
            "expected_content": "fallback",
            "expected_json": None,
            "created_at": "2026-06-10 09:05:00+00",
        },
    ]


def _seed_legacy_documents(session, rows: list[dict]) -> dict[str, dict]:
    """Insert one application + one legacy document per row; return key -> ids."""
    ids: dict[str, dict] = {}
    for row in rows:
        application_id = uuid.uuid4()
        document_id = uuid.uuid4()
        ids[row["key"]] = {
            "application_id": application_id,
            "document_id": document_id,
        }
        session.execute(
            text("INSERT INTO applications (id) VALUES (CAST(:id AS uuid))"),
            {"id": str(application_id)},
        )
        session.execute(
            text(
                """
                INSERT INTO documents (
                    id, application_id, doc_type, content, content_json, version,
                    created_at, updated_at
                )
                VALUES (
                    CAST(:id AS uuid),
                    CAST(:application_id AS uuid),
                    :doc_type,
                    :content,
                    CAST(:content_json AS jsonb),
                    :version,
                    :created_at,
                    :created_at
                )
                """
            ),
            {
                "id": str(document_id),
                "application_id": str(application_id),
                "doc_type": row["doc_type"],
                "content": row["content"],
                "content_json": (
                    json.dumps(row["content_json"])
                    if row["content_json"] is not None
                    else None
                ),
                "version": row["version"],
                "created_at": row["created_at"],
            },
        )
    return ids


def test_backfill_preserves_every_legacy_document(db_session, monkeypatch) -> None:
    """Each legacy row yields exactly one logical document, version, and attachment."""
    migration = _load_migration_module()
    _isolate_schema(db_session)
    _create_m5_tables(db_session, with_doc_type_check=False)

    rows = _representative_legacy_rows()
    ids = _seed_legacy_documents(db_session, rows)

    monkeypatch.setattr(migration.op, "get_bind", db_session.connection)
    migration._backfill_legacy_documents()

    # Exactly one version and one attachment per legacy document.
    assert db_session.execute(text("SELECT count(*) FROM document_versions")).scalar_one() == len(rows)
    assert db_session.execute(text("SELECT count(*) FROM application_documents")).scalar_one() == len(rows)

    for row in rows:
        document_id = ids[row["key"]]["document_id"]
        application_id = ids[row["key"]]["application_id"]

        document = db_session.execute(
            text(
                """
                SELECT doc_type, name, updated_at, created_at
                FROM documents WHERE id = CAST(:id AS uuid)
                """
            ),
            {"id": str(document_id)},
        ).mappings().one()
        assert document["doc_type"] == row["expected_type"]
        assert document["name"] == row["expected_name"]
        assert document["updated_at"] == document["created_at"]

        version = db_session.execute(
            text(
                """
                SELECT version_number, content, content_json, checksum
                FROM document_versions WHERE document_id = CAST(:id AS uuid)
                """
            ),
            {"id": str(document_id)},
        ).mappings().one()
        assert version["version_number"] == row["expected_version"]
        assert version["content"] == row["expected_content"]
        assert version["content_json"] == row["expected_json"]
        assert version["checksum"] == _expected_checksum(
            row["expected_content"], row["expected_json"]
        )

        attachment = db_session.execute(
            text(
                """
                SELECT ad.role, ad.display_order, ad.application_id, ad.created_at
                FROM application_documents ad
                JOIN document_versions dv ON dv.id = ad.document_version_id
                WHERE dv.document_id = CAST(:id AS uuid)
                """
            ),
            {"id": str(document_id)},
        ).mappings().one()
        assert attachment["role"] == row["expected_type"]
        assert attachment["display_order"] == 0
        assert attachment["application_id"] == application_id

    # The reconciled doc_type values all satisfy the canonical CHECK.
    db_session.execute(
        text(
            f"ALTER TABLE documents ADD CONSTRAINT ck_documents_doc_type_m5 "
            f"CHECK ({_DOC_TYPE_CHECK})"
        )
    )


def test_backfill_is_idempotent_on_rerun(db_session, monkeypatch) -> None:
    """Re-running the backfill does not create duplicate versions or attachments."""
    migration = _load_migration_module()
    _isolate_schema(db_session)
    _create_m5_tables(db_session, with_doc_type_check=False)

    rows = _representative_legacy_rows()
    _seed_legacy_documents(db_session, rows)

    monkeypatch.setattr(migration.op, "get_bind", db_session.connection)
    migration._backfill_legacy_documents()
    migration._backfill_legacy_documents()

    assert db_session.execute(text("SELECT count(*) FROM document_versions")).scalar_one() == len(rows)
    assert db_session.execute(text("SELECT count(*) FROM application_documents")).scalar_one() == len(rows)


def test_restrict_foreign_keys_protect_history(db_session) -> None:
    """ON DELETE RESTRICT preserves version, attachment, and answer provenance."""
    _isolate_schema(db_session)
    _create_m5_tables(db_session, with_doc_type_check=True)

    application_id = uuid.uuid4()
    document_id = uuid.uuid4()
    version_id = uuid.uuid4()
    library_id = uuid.uuid4()

    db_session.execute(
        text("INSERT INTO applications (id) VALUES (CAST(:id AS uuid))"),
        {"id": str(application_id)},
    )
    db_session.execute(
        text(
            """
            INSERT INTO documents (id, application_id, doc_type, name, content, version)
            VALUES (CAST(:id AS uuid), CAST(:app AS uuid), 'resume', 'Resume', 'x', 1)
            """
        ),
        {"id": str(document_id), "app": str(application_id)},
    )
    db_session.execute(
        text(
            """
            INSERT INTO document_versions (id, document_id, version_number, content, checksum)
            VALUES (CAST(:id AS uuid), CAST(:doc AS uuid), 1, 'x', 'sum')
            """
        ),
        {"id": str(version_id), "doc": str(document_id)},
    )
    db_session.execute(
        text(
            """
            INSERT INTO application_documents (
                id, application_id, document_version_id, role, display_order
            )
            VALUES (CAST(:id AS uuid), CAST(:app AS uuid), CAST(:ver AS uuid), 'resume', 0)
            """
        ),
        {"id": str(uuid.uuid4()), "app": str(application_id), "ver": str(version_id)},
    )
    db_session.execute(
        text(
            """
            INSERT INTO answer_library (id, question_key, question_text, answer_text)
            VALUES (CAST(:id AS uuid), 'work_auth', 'Authorized?', 'Yes')
            """
        ),
        {"id": str(library_id)},
    )
    db_session.execute(
        text(
            """
            INSERT INTO application_answers (
                id, application_id, answer_library_id, question_key, question_text, answer_text
            )
            VALUES (
                CAST(:id AS uuid), CAST(:app AS uuid), CAST(:lib AS uuid),
                'work_auth', 'Authorized?', 'Yes'
            )
            """
        ),
        {"id": str(uuid.uuid4()), "app": str(application_id), "lib": str(library_id)},
    )

    # A version that is still attached cannot be deleted.
    _assert_restricted(
        db_session,
        "DELETE FROM document_versions WHERE id = CAST(:id AS uuid)",
        {"id": str(version_id)},
    )
    # A logical document with versions cannot be deleted.
    _assert_restricted(
        db_session,
        "DELETE FROM documents WHERE id = CAST(:id AS uuid)",
        {"id": str(document_id)},
    )
    # An application referenced by attachment/answer history cannot be deleted.
    _assert_restricted(
        db_session,
        "DELETE FROM applications WHERE id = CAST(:id AS uuid)",
        {"id": str(application_id)},
    )
    # A library answer with a recorded snapshot cannot be deleted.
    _assert_restricted(
        db_session,
        "DELETE FROM answer_library WHERE id = CAST(:id AS uuid)",
        {"id": str(library_id)},
    )


def test_constraints_reject_invalid_writes(db_session) -> None:
    """PostgreSQL rejects every contract-invalid write."""
    _isolate_schema(db_session)
    _create_m5_tables(db_session, with_doc_type_check=True)

    application_id = uuid.uuid4()
    document_id = uuid.uuid4()
    version_id = uuid.uuid4()
    db_session.execute(
        text("INSERT INTO applications (id) VALUES (CAST(:id AS uuid))"),
        {"id": str(application_id)},
    )
    db_session.execute(
        text(
            """
            INSERT INTO documents (id, application_id, doc_type, name, content, version)
            VALUES (CAST(:id AS uuid), CAST(:app AS uuid), 'resume', 'Resume', 'x', 1)
            """
        ),
        {"id": str(document_id), "app": str(application_id)},
    )
    db_session.execute(
        text(
            """
            INSERT INTO document_versions (id, document_id, version_number, content, checksum)
            VALUES (CAST(:id AS uuid), CAST(:doc AS uuid), 1, 'x', 'sum')
            """
        ),
        {"id": str(version_id), "doc": str(document_id)},
    )

    # Blank document name.
    _assert_rejected(
        db_session,
        """
        INSERT INTO documents (id, application_id, doc_type, name, content, version)
        VALUES (CAST(:id AS uuid), CAST(:app AS uuid), 'resume', '', 'x', 1)
        """,
        {"id": str(uuid.uuid4()), "app": str(application_id)},
    )
    # Invalid document type.
    _assert_rejected(
        db_session,
        """
        INSERT INTO documents (id, application_id, doc_type, name, content, version)
        VALUES (CAST(:id AS uuid), CAST(:app AS uuid), 'bogus', 'Doc', 'x', 1)
        """,
        {"id": str(uuid.uuid4()), "app": str(application_id)},
    )
    # Non-positive version number.
    _assert_rejected(
        db_session,
        """
        INSERT INTO document_versions (id, document_id, version_number, content, checksum)
        VALUES (CAST(:id AS uuid), CAST(:doc AS uuid), 0, 'x', 'sum')
        """,
        {"id": str(uuid.uuid4()), "doc": str(document_id)},
    )
    # Missing version payload (both null).
    _assert_rejected(
        db_session,
        """
        INSERT INTO document_versions (id, document_id, version_number, content, content_json, checksum)
        VALUES (CAST(:id AS uuid), CAST(:doc AS uuid), 5, NULL, NULL, 'sum')
        """,
        {"id": str(uuid.uuid4()), "doc": str(document_id)},
    )
    # Duplicate version_number per document.
    _assert_rejected(
        db_session,
        """
        INSERT INTO document_versions (id, document_id, version_number, content, checksum)
        VALUES (CAST(:id AS uuid), CAST(:doc AS uuid), 1, 'y', 'sum2')
        """,
        {"id": str(uuid.uuid4()), "doc": str(document_id)},
    )
    # Invalid attachment role.
    _assert_rejected(
        db_session,
        """
        INSERT INTO application_documents (id, application_id, document_version_id, role, display_order)
        VALUES (CAST(:id AS uuid), CAST(:app AS uuid), CAST(:ver AS uuid), 'bogus', 0)
        """,
        {"id": str(uuid.uuid4()), "app": str(application_id), "ver": str(version_id)},
    )

    # Duplicate identical attachment (application, version, role).
    db_session.execute(
        text(
            """
            INSERT INTO application_documents (id, application_id, document_version_id, role, display_order)
            VALUES (CAST(:id AS uuid), CAST(:app AS uuid), CAST(:ver AS uuid), 'resume', 0)
            """
        ),
        {"id": str(uuid.uuid4()), "app": str(application_id), "ver": str(version_id)},
    )
    _assert_rejected(
        db_session,
        """
        INSERT INTO application_documents (id, application_id, document_version_id, role, display_order)
        VALUES (CAST(:id AS uuid), CAST(:app AS uuid), CAST(:ver AS uuid), 'resume', 1)
        """,
        {"id": str(uuid.uuid4()), "app": str(application_id), "ver": str(version_id)},
    )

    # Duplicate active answer-library key.
    db_session.execute(
        text(
            """
            INSERT INTO answer_library (id, question_key, question_text, answer_text)
            VALUES (CAST(:id AS uuid), 'work_auth', 'Authorized?', 'Yes')
            """
        ),
        {"id": str(uuid.uuid4())},
    )
    _assert_rejected(
        db_session,
        """
        INSERT INTO answer_library (id, question_key, question_text, answer_text)
        VALUES (CAST(:id AS uuid), 'work_auth', 'Authorized again?', 'Yes')
        """,
        {"id": str(uuid.uuid4())},
    )

    # Duplicate per-application answer key.
    db_session.execute(
        text(
            """
            INSERT INTO application_answers (id, application_id, question_key, question_text, answer_text)
            VALUES (CAST(:id AS uuid), CAST(:app AS uuid), 'visa', 'Visa?', 'No')
            """
        ),
        {"id": str(uuid.uuid4()), "app": str(application_id)},
    )
    _assert_rejected(
        db_session,
        """
        INSERT INTO application_answers (id, application_id, question_key, question_text, answer_text)
        VALUES (CAST(:id AS uuid), CAST(:app AS uuid), 'visa', 'Visa again?', 'No')
        """,
        {"id": str(uuid.uuid4()), "app": str(application_id)},
    )


def test_archived_answer_key_can_be_reused(db_session) -> None:
    """The partial unique index frees the key once the prior row is archived."""
    _isolate_schema(db_session)
    _create_m5_tables(db_session, with_doc_type_check=True)

    db_session.execute(
        text(
            """
            INSERT INTO answer_library (id, question_key, question_text, answer_text, is_archived)
            VALUES (CAST(:id AS uuid), 'relocate', 'Relocate?', 'Yes', true)
            """
        ),
        {"id": str(uuid.uuid4())},
    )
    # A new active row may take the key now that the prior one is archived.
    db_session.execute(
        text(
            """
            INSERT INTO answer_library (id, question_key, question_text, answer_text)
            VALUES (CAST(:id AS uuid), 'relocate', 'Relocate?', 'No')
            """
        ),
        {"id": str(uuid.uuid4())},
    )
    active = db_session.execute(
        text(
            "SELECT count(*) FROM answer_library "
            "WHERE question_key = 'relocate' AND is_archived IS false"
        )
    ).scalar_one()
    assert active == 1


def _assert_restricted(session, statement: str, params: dict) -> None:
    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.execute(text(statement), params)


def _assert_rejected(session, statement: str, params: dict) -> None:
    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.execute(text(statement), params)


def _load_migration_module():
    migration_path = (
        Path(__file__).parents[2]
        / "alembic"
        / "versions"
        / "0012_add_m5_document_answer_schema.py"
    )
    spec = importlib.util.spec_from_file_location("m5_document_answer_migration", migration_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
