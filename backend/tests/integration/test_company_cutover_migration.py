"""Regression coverage for the M3 company identity cutover migration.

Requires PostgreSQL with migrations already applied (alembic upgrade head).
Skipped automatically at runtime when the database is unreachable.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from applypilot.config.settings import get_settings

_CONNECT_TIMEOUT = 2


@pytest.fixture()
def db_session():
    """Connect to PostgreSQL and yield a transactional session."""
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


def test_0011_backfills_jobs_created_after_0010_before_non_null_cutover(
    db_session,
    monkeypatch,
) -> None:
    """Jobs inserted after 0010 still receive company_id before 0011 enforces NOT NULL."""
    migration = _load_migration_module("0011_complete_company_identity_cutover.py")
    schema_name = f"migration_regression_{uuid.uuid4().hex}"
    existing_company_id = uuid.uuid4()
    first_job_id = uuid.uuid4()
    second_job_id = uuid.uuid4()
    unknown_job_id = uuid.uuid4()
    confidential_job_id = uuid.uuid4()
    existing_job_id = uuid.uuid4()

    db_session.execute(text(f'CREATE SCHEMA "{schema_name}"'))
    db_session.execute(text(f'SET LOCAL search_path TO "{schema_name}"'))
    db_session.execute(
        text(
            """
            CREATE TABLE companies (
                id uuid PRIMARY KEY,
                name varchar(256) NOT NULL,
                normalized_name varchar(256) NOT NULL,
                domain varchar(256),
                normalized_domain varchar(256)
            )
            """
        )
    )
    db_session.execute(
        text(
            """
            CREATE TABLE jobs (
                id uuid PRIMARY KEY,
                company varchar(256),
                company_id uuid REFERENCES companies(id),
                created_at timestamptz NOT NULL DEFAULT now()
            )
            """
        )
    )
    db_session.execute(
        text(
            """
            INSERT INTO companies (
                id,
                name,
                normalized_name,
                domain,
                normalized_domain
            )
            VALUES (
                CAST(:company_id AS uuid),
                'Existing Company',
                'existing company',
                NULL,
                NULL
            )
            """
        ),
        {"company_id": str(existing_company_id)},
    )
    db_session.execute(
        text(
            """
            INSERT INTO jobs (id, company, company_id, created_at)
            VALUES
                (
                    CAST(:first_job_id AS uuid),
                    'ApplyPilot, Inc.',
                    NULL,
                    '2026-06-15 12:00:00+00'
                ),
                (
                    CAST(:second_job_id AS uuid),
                    'applypilot inc',
                    NULL,
                    '2026-06-15 12:01:00+00'
                ),
                (
                    CAST(:unknown_job_id AS uuid),
                    NULL,
                    NULL,
                    '2026-06-15 12:02:00+00'
                ),
                (
                    CAST(:confidential_job_id AS uuid),
                    'Confidential employer',
                    NULL,
                    '2026-06-15 12:03:00+00'
                ),
                (
                    CAST(:existing_job_id AS uuid),
                    'Existing Company',
                    CAST(:existing_company_id AS uuid),
                    '2026-06-15 12:04:00+00'
                )
            """
        ),
        {
            "first_job_id": str(first_job_id),
            "second_job_id": str(second_job_id),
            "unknown_job_id": str(unknown_job_id),
            "confidential_job_id": str(confidential_job_id),
            "existing_job_id": str(existing_job_id),
            "existing_company_id": str(existing_company_id),
        },
    )

    monkeypatch.setattr(migration.op, "get_bind", db_session.connection)

    migration._backfill_remaining_jobs()

    rows = {
        row.id: row
        for row in db_session.execute(
            text(
                """
                SELECT
                    jobs.id,
                    jobs.company,
                    jobs.company_id,
                    companies.name AS resolved_company_name,
                    companies.normalized_name AS resolved_normalized_name
                FROM jobs
                JOIN companies ON companies.id = jobs.company_id
                ORDER BY jobs.id
                """
            )
        )
    }

    assert rows[first_job_id].company_id == rows[second_job_id].company_id
    assert rows[first_job_id].resolved_company_name == "ApplyPilot, Inc."
    assert rows[first_job_id].resolved_normalized_name == "applypilot inc"
    assert rows[unknown_job_id].resolved_company_name == "Unknown Company"
    assert rows[unknown_job_id].resolved_normalized_name == "unknown company"
    assert rows[confidential_job_id].resolved_company_name == "Confidential Company"
    assert rows[confidential_job_id].resolved_normalized_name == "confidential company"
    assert rows[existing_job_id].company_id == existing_company_id
    assert all(row.company_id is not None for row in rows.values())


def _load_migration_module(filename: str):
    migration_path = Path(__file__).parents[2] / "alembic" / "versions" / filename
    spec = importlib.util.spec_from_file_location("company_cutover_migration", migration_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
