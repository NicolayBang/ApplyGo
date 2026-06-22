"""Regression coverage for the M5 legacy-compatibility removal (migration 0014).

Migration ``0014`` removes the legacy single-application compatibility surface from
``documents`` (the ``application_id`` foreign key + index and the ``application_id``,
``content``, ``content_json``, and ``version`` columns) after the M5 read-model API
switched off them. It first re-runs the preservation invariant and aborts *before any
DDL* if a legacy-owned document is not fully represented in the immutable
``document_versions`` / append-only ``application_documents`` model.

Each test runs inside a throwaway PostgreSQL schema and is skipped automatically when
the database is unreachable. The schema here mirrors the post-``0013`` ``documents`` +
M5 tables so the ``0014`` cleanup can be exercised in isolation, following the
established pattern in ``test_m5_document_library_nullability.py``. The full
``alembic upgrade head`` path through ``0014`` is validated separately by the
migration/quality-gate suite, and ``0014``'s revision wiring and forward-only downgrade
are asserted directly below. The real migration guard
``_assert_legacy_rows_preserved`` is invoked against live data rather than reimplemented.
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

# The exact DDL migration 0014 issues after its preservation guard passes.
_DROP_FK = "ALTER TABLE documents DROP CONSTRAINT documents_application_id_fkey"
_DROP_INDEX = "DROP INDEX ix_documents_application_id"
_LEGACY_COLUMNS = ("application_id", "content", "content_json", "version")
_RETAINED_COLUMNS = {"id", "doc_type", "name", "is_archived", "created_at", "updated_at"}

_MIGRATION = "0014_remove_documents_legacy_compatibility.py"


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
    spec = importlib.util.spec_from_file_location("document_cleanup_migration", migration_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _isolate_schema(session) -> str:
    schema_name = f"m5_cleanup_regression_{uuid.uuid4().hex}"
    session.execute(text(f'CREATE SCHEMA "{schema_name}"'))
    session.execute(text(f'SET LOCAL search_path TO "{schema_name}"'))
    return schema_name


def _create_post_0013_tables(session) -> None:
    """Create the post-0013 documents + M5 tables (application_id is now NULLABLE)."""
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
                application_id uuid
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
    session.execute(
        text(
            """
            CREATE TABLE application_packet_reviews (
                id uuid PRIMARY KEY,
                application_id uuid NOT NULL REFERENCES applications(id),
                decision varchar(32) NOT NULL,
                reviewed_by varchar(64) NOT NULL,
                source varchar(32) NOT NULL,
                packet_text text,
                notes text,
                created_at timestamptz NOT NULL DEFAULT now()
            )
            """
        )
    )


def _seed_application(session) -> uuid.UUID:
    application_id = uuid.uuid4()
    session.execute(
        text("INSERT INTO applications (id) VALUES (CAST(:id AS uuid))"),
        {"id": str(application_id)},
    )
    return application_id


def _seed_backfilled_legacy_document(session, application_id: uuid.UUID) -> dict[str, uuid.UUID]:
    """Seed a legacy-owned document with its 0012 backfilled version + attachment."""
    ids = {
        "document_id": uuid.uuid4(),
        "version_id": uuid.uuid4(),
        "attachment_id": uuid.uuid4(),
    }
    session.execute(
        text(
            """
            INSERT INTO documents (id, application_id, doc_type, content, version, name)
            VALUES (CAST(:id AS uuid), CAST(:app AS uuid), 'resume', 'Legacy resume body', 1,
                    'Legacy resume')
            """
        ),
        {"id": str(ids["document_id"]), "app": str(application_id)},
    )
    session.execute(
        text(
            """
            INSERT INTO document_versions (id, document_id, version_number, content, checksum)
            VALUES (CAST(:id AS uuid), CAST(:doc AS uuid), 1, 'Legacy resume body',
                    'legacy-checksum')
            """
        ),
        {"id": str(ids["version_id"]), "doc": str(ids["document_id"])},
    )
    session.execute(
        text(
            """
            INSERT INTO application_documents
                (id, application_id, document_version_id, role, display_order)
            VALUES (CAST(:id AS uuid), CAST(:app AS uuid), CAST(:ver AS uuid), 'resume', 0)
            """
        ),
        {
            "id": str(ids["attachment_id"]),
            "app": str(application_id),
            "ver": str(ids["version_id"]),
        },
    )
    return ids


def _seed_standalone_m5_document(session, application_id: uuid.UUID) -> dict[str, uuid.UUID]:
    """Seed a new reusable library document (application_id NULL) with version + attachment."""
    ids = {
        "document_id": uuid.uuid4(),
        "version_id": uuid.uuid4(),
        "attachment_id": uuid.uuid4(),
    }
    session.execute(
        text(
            """
            INSERT INTO documents (id, doc_type, name)
            VALUES (CAST(:id AS uuid), 'cover_letter', 'Reusable cover letter')
            """
        ),
        {"id": str(ids["document_id"])},
    )
    session.execute(
        text(
            """
            INSERT INTO document_versions (id, document_id, version_number, content_json, checksum)
            VALUES (CAST(:id AS uuid), CAST(:doc AS uuid), 2,
                    CAST('{"body": "Reusable"}' AS jsonb), 'standalone-checksum')
            """
        ),
        {"id": str(ids["version_id"]), "doc": str(ids["document_id"])},
    )
    session.execute(
        text(
            """
            INSERT INTO application_documents
                (id, application_id, document_version_id, role, display_order)
            VALUES (CAST(:id AS uuid), CAST(:app AS uuid), CAST(:ver AS uuid), 'cover_letter', 1)
            """
        ),
        {
            "id": str(ids["attachment_id"]),
            "app": str(application_id),
            "ver": str(ids["version_id"]),
        },
    )
    return ids


def _apply_cleanup(session, migration) -> None:
    """Run the real preservation guard, then the migration's destructive DDL."""
    migration._assert_legacy_rows_preserved(session)
    session.execute(text(_DROP_FK))
    session.execute(text(_DROP_INDEX))
    for column in _LEGACY_COLUMNS:
        session.execute(text(f"ALTER TABLE documents DROP COLUMN {column}"))


def _document_columns(session) -> set[str]:
    rows = session.execute(
        text(
            """
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = current_schema() AND table_name = 'documents'
            """
        )
    ).scalars().all()
    return set(rows)


def test_migration_0014_revision_wiring_and_forward_only_downgrade() -> None:
    """Migration 0014 chains from 0013 and refuses any downgrade."""
    migration = _load_migration_module(_MIGRATION)

    assert migration.revision == "0014"
    assert migration.down_revision == "0013"

    with pytest.raises(RuntimeError, match="forward-only"):
        migration.downgrade()


def test_backfilled_legacy_and_standalone_documents_survive_cleanup(db_session) -> None:
    """A backfilled legacy doc and a standalone M5 doc keep their version/attachment truth."""
    migration = _load_migration_module(_MIGRATION)
    _isolate_schema(db_session)
    _create_post_0013_tables(db_session)
    app_id = _seed_application(db_session)
    legacy = _seed_backfilled_legacy_document(db_session, app_id)
    standalone = _seed_standalone_m5_document(db_session, app_id)

    _apply_cleanup(db_session, migration)

    # Both logical-library rows survive with only the retained identity columns.
    surviving = db_session.execute(
        text("SELECT id, doc_type, name, is_archived FROM documents ORDER BY name")
    ).mappings().all()
    by_id = {row["id"]: row for row in surviving}
    assert by_id[legacy["document_id"]]["doc_type"] == "resume"
    assert by_id[legacy["document_id"]]["name"] == "Legacy resume"
    assert by_id[standalone["document_id"]]["doc_type"] == "cover_letter"
    assert by_id[standalone["document_id"]]["is_archived"] is False

    # Immutable version payloads are intact for both documents.
    legacy_version = db_session.execute(
        text(
            "SELECT document_id, version_number, content, checksum FROM document_versions "
            "WHERE id = CAST(:id AS uuid)"
        ),
        {"id": str(legacy["version_id"])},
    ).one()
    assert legacy_version.document_id == legacy["document_id"]
    assert legacy_version.version_number == 1
    assert legacy_version.content == "Legacy resume body"
    assert legacy_version.checksum == "legacy-checksum"

    standalone_version = db_session.execute(
        text(
            "SELECT version_number, content_json, checksum FROM document_versions "
            "WHERE id = CAST(:id AS uuid)"
        ),
        {"id": str(standalone["version_id"])},
    ).one()
    assert standalone_version.version_number == 2
    assert standalone_version.content_json == {"body": "Reusable"}
    assert standalone_version.checksum == "standalone-checksum"

    # Attachments still bind each application to its exact version.
    attachments = db_session.execute(
        text(
            "SELECT document_version_id, role FROM application_documents "
            "WHERE application_id = CAST(:app AS uuid) ORDER BY display_order"
        ),
        {"app": str(app_id)},
    ).mappings().all()
    assert [(a["document_version_id"], a["role"]) for a in attachments] == [
        (legacy["version_id"], "resume"),
        (standalone["version_id"], "cover_letter"),
    ]


def test_retired_columns_index_and_fk_no_longer_exist(db_session) -> None:
    """After cleanup, the legacy columns, index, and foreign key are gone."""
    migration = _load_migration_module(_MIGRATION)
    _isolate_schema(db_session)
    _create_post_0013_tables(db_session)
    app_id = _seed_application(db_session)
    _seed_backfilled_legacy_document(db_session, app_id)

    _apply_cleanup(db_session, migration)

    columns = _document_columns(db_session)
    assert columns == _RETAINED_COLUMNS
    assert set(_LEGACY_COLUMNS).isdisjoint(columns)

    index_present = db_session.execute(
        text(
            "SELECT 1 FROM pg_indexes "
            "WHERE schemaname = current_schema() AND indexname = 'ix_documents_application_id'"
        )
    ).first()
    assert index_present is None

    fk_present = db_session.execute(
        text(
            "SELECT 1 FROM pg_constraint "
            "WHERE conrelid = (current_schema() || '.documents')::regclass AND contype = 'f'"
        )
    ).first()
    assert fk_present is None


def test_inconsistent_legacy_data_blocks_migration_without_partial_application(db_session) -> None:
    """A legacy-owned doc missing its M5 representation aborts the guard before any DDL."""
    migration = _load_migration_module(_MIGRATION)
    _isolate_schema(db_session)
    _create_post_0013_tables(db_session)
    app_id = _seed_application(db_session)

    # Legacy-owned document with NO matching version or attachment.
    orphan_id = uuid.uuid4()
    db_session.execute(
        text(
            """
            INSERT INTO documents (id, application_id, doc_type, content, version, name)
            VALUES (CAST(:id AS uuid), CAST(:app AS uuid), 'resume', 'Orphan body', 1, 'Orphan')
            """
        ),
        {"id": str(orphan_id), "app": str(app_id)},
    )

    with pytest.raises(RuntimeError, match="lack a matching"):
        migration._assert_legacy_rows_preserved(db_session)

    # The guard raised before any DDL: the legacy columns are still present.
    assert set(_LEGACY_COLUMNS).issubset(_document_columns(db_session))


def test_m5_deletion_restrictions_and_packet_review_survive_cleanup(db_session) -> None:
    """ON DELETE RESTRICT and M2 packet-review evidence remain intact after cleanup."""
    migration = _load_migration_module(_MIGRATION)
    _isolate_schema(db_session)
    _create_post_0013_tables(db_session)
    app_id = _seed_application(db_session)
    legacy = _seed_backfilled_legacy_document(db_session, app_id)

    review_id = uuid.uuid4()
    db_session.execute(
        text(
            """
            INSERT INTO application_packet_reviews
                (id, application_id, decision, reviewed_by, source, packet_text)
            VALUES (CAST(:id AS uuid), CAST(:app AS uuid), 'approved', 'reviewer', 'dashboard',
                    'packet snapshot')
            """
        ),
        {"id": str(review_id), "app": str(app_id)},
    )

    _apply_cleanup(db_session, migration)

    # A logical document cannot be deleted while immutable versions reference it.
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.execute(
                text("DELETE FROM documents WHERE id = CAST(:id AS uuid)"),
                {"id": str(legacy["document_id"])},
            )

    # An immutable version cannot be deleted while an attachment references it.
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.execute(
                text("DELETE FROM document_versions WHERE id = CAST(:id AS uuid)"),
                {"id": str(legacy["version_id"])},
            )

    # M2 packet-review evidence is untouched by the documents cleanup.
    review = db_session.execute(
        text(
            "SELECT decision, reviewed_by, source, packet_text FROM application_packet_reviews "
            "WHERE id = CAST(:id AS uuid)"
        ),
        {"id": str(review_id)},
    ).one()
    assert review.decision == "approved"
    assert review.source == "dashboard"
    assert review.packet_text == "packet snapshot"
