"""Regression coverage for the M5 document-library nullability fix (migration 0013).

Migration ``0013`` relaxes ``documents.application_id`` to ``NULL``-able so reusable
logical-library documents may be created without an owning application, while legacy
rows, the foreign key, index, and ``ON DELETE CASCADE`` behavior are preserved during
the M5 compatibility window.

Each test runs inside a throwaway PostgreSQL schema and is skipped automatically when
the database is unreachable. The schema here mirrors the post-``0012`` ``documents`` +
M5 tables so the ``0013`` nullability change can be exercised in isolation, following
the established pattern in ``test_m5_document_answer_migration.py``. The full
``alembic upgrade head`` path is validated separately by the migration/quality-gate
suite, and ``0013``'s revision wiring is asserted directly below.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from applypilot.config.settings import get_settings

_CONNECT_TIMEOUT = 2

# The exact metadata-only DDL migration 0013 applies via op.alter_column(nullable=True).
_DROP_NOT_NULL = "ALTER TABLE documents ALTER COLUMN application_id DROP NOT NULL"


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


def _load_migration_module(filename: str):
    migration_path = Path(__file__).parents[2] / "alembic" / "versions" / filename
    spec = importlib.util.spec_from_file_location("document_nullability_migration", migration_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _isolate_schema(session) -> str:
    schema_name = f"m5_nullability_regression_{uuid.uuid4().hex}"
    session.execute(text(f'CREATE SCHEMA "{schema_name}"'))
    session.execute(text(f'SET LOCAL search_path TO "{schema_name}"'))
    return schema_name


def _create_post_0012_tables(session) -> None:
    """Create the post-0012 documents + M5 tables (application_id still NOT NULL)."""
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
    session.execute(
        text(
            """
            CREATE TABLE documents (
                id uuid PRIMARY KEY,
                application_id uuid NOT NULL
                    REFERENCES applications(id) ON DELETE CASCADE,
                doc_type varchar(64) NOT NULL,
                content text,
                content_json jsonb,
                version integer NOT NULL DEFAULT 1,
                name varchar(256) NOT NULL,
                is_archived boolean NOT NULL DEFAULT false,
                created_at timestamptz NOT NULL DEFAULT now(),
                updated_at timestamptz NOT NULL DEFAULT now(),
                CONSTRAINT ck_documents_doc_type_m5
                    CHECK (doc_type IN ('resume', 'cover_letter', 'supporting', 'other')),
                CONSTRAINT ck_documents_name_not_blank_m5 CHECK (name <> '')
            )
            """
        )
    )
    session.execute(text("CREATE INDEX ix_documents_application_id ON documents (application_id)"))
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
                created_at timestamptz NOT NULL DEFAULT now()
            )
            """
        )
    )
    session.execute(
        text(
            """
            CREATE TABLE application_documents (
                id uuid PRIMARY KEY,
                application_id uuid NOT NULL
                    REFERENCES applications(id) ON DELETE RESTRICT,
                document_version_id uuid NOT NULL
                    REFERENCES document_versions(id) ON DELETE RESTRICT,
                role varchar(64) NOT NULL,
                display_order integer NOT NULL,
                created_at timestamptz NOT NULL DEFAULT now()
            )
            """
        )
    )


def _seed_legacy_document(session) -> dict[str, uuid.UUID]:
    """Seed one legacy application/document/version/attachment (mirrors the 0012 backfill)."""
    ids = {
        "application_id": uuid.uuid4(),
        "document_id": uuid.uuid4(),
        "version_id": uuid.uuid4(),
        "attachment_id": uuid.uuid4(),
    }
    session.execute(
        text("INSERT INTO applications (id) VALUES (CAST(:id AS uuid))"),
        {"id": str(ids["application_id"])},
    )
    session.execute(
        text(
            """
            INSERT INTO documents (id, application_id, doc_type, content, version, name)
            VALUES (
                CAST(:id AS uuid),
                CAST(:application_id AS uuid),
                'resume',
                'Legacy resume body',
                1,
                'Legacy resume'
            )
            """
        ),
        {"id": str(ids["document_id"]), "application_id": str(ids["application_id"])},
    )
    session.execute(
        text(
            """
            INSERT INTO document_versions (
                id, document_id, version_number, content, checksum
            )
            VALUES (
                CAST(:id AS uuid),
                CAST(:document_id AS uuid),
                1,
                'Legacy resume body',
                'legacy-checksum'
            )
            """
        ),
        {"id": str(ids["version_id"]), "document_id": str(ids["document_id"])},
    )
    session.execute(
        text(
            """
            INSERT INTO application_documents (
                id, application_id, document_version_id, role, display_order
            )
            VALUES (
                CAST(:id AS uuid),
                CAST(:application_id AS uuid),
                CAST(:version_id AS uuid),
                'resume',
                0
            )
            """
        ),
        {
            "id": str(ids["attachment_id"]),
            "application_id": str(ids["application_id"]),
            "version_id": str(ids["version_id"]),
        },
    )
    return ids


def test_migration_0013_revision_wiring_is_correct() -> None:
    """Migration 0013 chains from 0012 and relaxes documents.application_id to nullable."""
    migration = _load_migration_module("0013_make_documents_application_id_nullable.py")

    assert migration.revision == "0013"
    assert migration.down_revision == "0012"


def test_legacy_rows_and_backfilled_m5_records_survive_nullability_change(db_session) -> None:
    """Legacy application IDs and backfilled version/attachment records are preserved."""
    _isolate_schema(db_session)
    _create_post_0012_tables(db_session)
    ids = _seed_legacy_document(db_session)

    db_session.execute(text(_DROP_NOT_NULL))

    document = db_session.execute(
        text(
            """
            SELECT application_id, doc_type, content, version, name
            FROM documents
            WHERE id = CAST(:id AS uuid)
            """
        ),
        {"id": str(ids["document_id"])},
    ).one()
    assert document.application_id == ids["application_id"]
    assert document.doc_type == "resume"
    assert document.content == "Legacy resume body"
    assert document.version == 1
    assert document.name == "Legacy resume"

    version = db_session.execute(
        text(
            """
            SELECT document_id, version_number, content, checksum
            FROM document_versions
            WHERE id = CAST(:id AS uuid)
            """
        ),
        {"id": str(ids["version_id"])},
    ).one()
    assert version.document_id == ids["document_id"]
    assert version.version_number == 1
    assert version.content == "Legacy resume body"
    assert version.checksum == "legacy-checksum"

    attachment = db_session.execute(
        text(
            """
            SELECT application_id, document_version_id, role, display_order
            FROM application_documents
            WHERE id = CAST(:id AS uuid)
            """
        ),
        {"id": str(ids["attachment_id"])},
    ).one()
    assert attachment.application_id == ids["application_id"]
    assert attachment.document_version_id == ids["version_id"]
    assert attachment.role == "resume"
    assert attachment.display_order == 0


def test_new_logical_document_may_have_null_application_id(db_session) -> None:
    """After 0013, a reusable logical document inserts with application_id = NULL."""
    _isolate_schema(db_session)
    _create_post_0012_tables(db_session)

    # Before the change the NOT NULL constraint rejects an owner-less document.
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.execute(
                text(
                    """
                    INSERT INTO documents (id, doc_type, name)
                    VALUES (gen_random_uuid(), 'resume', 'Reusable resume')
                    """
                )
            )

    db_session.execute(text(_DROP_NOT_NULL))

    document_id = uuid.uuid4()
    db_session.execute(
        text(
            """
            INSERT INTO documents (id, doc_type, name)
            VALUES (CAST(:id AS uuid), 'cover_letter', 'Reusable cover letter')
            """
        ),
        {"id": str(document_id)},
    )

    row = db_session.execute(
        text(
            """
            SELECT application_id, doc_type, name, is_archived
            FROM documents
            WHERE id = CAST(:id AS uuid)
            """
        ),
        {"id": str(document_id)},
    ).one()
    assert row.application_id is None
    assert row.doc_type == "cover_letter"
    assert row.name == "Reusable cover letter"
    assert row.is_archived is False


def test_nullability_change_rewrites_no_existing_data(db_session) -> None:
    """The metadata-only change deletes and rewrites no rows in any M5 table."""
    _isolate_schema(db_session)
    _create_post_0012_tables(db_session)
    ids = _seed_legacy_document(db_session)

    def snapshot() -> dict[str, int]:
        return {
            table: db_session.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()
            for table in (
                "applications",
                "documents",
                "document_versions",
                "application_documents",
            )
        }

    before = snapshot()
    db_session.execute(text(_DROP_NOT_NULL))
    after = snapshot()

    assert before == after
    # The legacy owning application reference is untouched (not rewritten to NULL).
    owner = db_session.execute(
        text("SELECT application_id FROM documents WHERE id = CAST(:id AS uuid)"),
        {"id": str(ids["document_id"])},
    ).scalar_one()
    assert owner == ids["application_id"]


def test_attachment_and_version_retention_constraints_still_hold(db_session) -> None:
    """ON DELETE RESTRICT still preserves attachment and version history after 0013."""
    _isolate_schema(db_session)
    _create_post_0012_tables(db_session)
    ids = _seed_legacy_document(db_session)
    db_session.execute(text(_DROP_NOT_NULL))

    # A logical document cannot be deleted while immutable versions reference it.
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.execute(
                text("DELETE FROM documents WHERE id = CAST(:id AS uuid)"),
                {"id": str(ids["document_id"])},
            )

    # An immutable version cannot be deleted while an application attachment references it.
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.execute(
                text("DELETE FROM document_versions WHERE id = CAST(:id AS uuid)"),
                {"id": str(ids["version_id"])},
            )
