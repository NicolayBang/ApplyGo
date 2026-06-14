"""DB-backed integration test: seed → audit API (seed-to-dashboard flow).

Validates that seed_demo_application() creates persisted records in PostgreSQL
and that the dashboard endpoints return complete audit and review summaries.

Requires PostgreSQL with migrations already applied (alembic upgrade head).
Skipped automatically at runtime when the database is unreachable.

Run explicitly:
    docker compose up -d postgres
    cd backend
    alembic upgrade head
    python -m pytest tests/integration/test_seed_to_dashboard.py -v
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from applypilot.config.settings import get_settings

# Short timeout (2s) so pytest collection never hangs when PG is absent.
_CONNECT_TIMEOUT = 2


@pytest.fixture()
def db_session():
    """Connect to PostgreSQL and yield a session; skip if PG is unreachable.

    Assumes migrations have already been applied via `alembic upgrade head`.
    Does NOT create tables itself — this validates the real migration path.
    """
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


def test_seed_creates_records_and_audit_api_returns_summary(db_session) -> None:
    """End-to-end: seed_demo_application persists records queryable via audit API."""
    from fastapi.testclient import TestClient

    from applypilot.db.dependencies import TrackerUnitOfWork, get_tracker_unit
    from applypilot.db.tracker import Tracker
    from applypilot.dev.demo_seed import seed_demo_application
    from applypilot.main import app

    # --- Seed using a real Tracker backed by PostgreSQL ---
    tracker = Tracker(db_session)
    result = seed_demo_application(tracker)
    db_session.commit()

    # --- Verify records exist in the database ---
    assert result.application_id is not None
    assert result.policy_decision_id is not None
    assert result.executor_action_id is not None

    application = tracker.get_application(result.application_id)
    assert application is not None
    assert application.state == "ApplicationCreated"

    events = tracker.get_events(result.application_id)
    assert len(events) >= 4  # created + policy + executor attempt + executor result
    event_types = [e.event_type for e in events]
    assert "application.created" in event_types
    assert "policy_decision_logged" in event_types
    assert "executor_attempt_logged" in event_types
    assert "executor_result_logged" in event_types

    policy_decisions = tracker.get_policy_decisions(result.application_id)
    assert len(policy_decisions) == 1
    assert policy_decisions[0].allowed is True
    assert policy_decisions[0].mode == "dry_run"

    executor_actions = tracker.get_executor_actions(result.application_id)
    assert len(executor_actions) == 1
    assert executor_actions[0].execution_mode == "dry_run"
    assert executor_actions[0].status == "planned"

    # --- Verify the audit API endpoint using the same session ---
    def override_tracker_unit():
        yield TrackerUnitOfWork(db_session)

    app.dependency_overrides[get_tracker_unit] = override_tracker_unit
    try:
        client = TestClient(app)
        response = client.get(f"/applications/{result.application_id}/audit")

        assert response.status_code == 200
        body = response.json()
        assert body["application"]["id"] == str(result.application_id)
        assert body["application"]["state"] == "ApplicationCreated"

        api_event_types = [e["event_type"] for e in body["events"]]
        assert "application.created" in api_event_types
        assert "policy_decision_logged" in api_event_types
        assert "executor_attempt_logged" in api_event_types
        assert "executor_result_logged" in api_event_types

        assert len(body["policy_decisions"]) == 1
        assert body["policy_decisions"][0]["allowed"] is True

        assert len(body["executor_actions"]) == 1
        assert body["executor_actions"][0]["status"] == "planned"
        assert body["executor_actions"][0]["execution_mode"] == "dry_run"

        review_response = client.get(f"/applications/{result.application_id}/review-summary")

        assert review_response.status_code == 200
        review_body = review_response.json()
        assert review_body["application"]["id"] == str(result.application_id)
        assert review_body["event_count"] >= 4
        assert review_body["latest_policy_decision"]["id"] == str(result.policy_decision_id)
        assert review_body["latest_policy_decision"]["allowed"] is True
        assert review_body["latest_executor_action"]["id"] == str(result.executor_action_id)
        assert review_body["latest_executor_action"]["status"] == "planned"
        assert review_body["ready_for_policy"] is False
        assert review_body["ready_for_dry_run"] is True
        assert review_body["ready_for_submission"] is False
        assert review_body["next_states"] == ["Draft"]
    finally:
        app.dependency_overrides.pop(get_tracker_unit, None)


def test_m1_value_check_constraints_reject_invalid_writes(db_session) -> None:
    """PostgreSQL rejects invalid stable M1 vocabulary values."""
    job_id = uuid.uuid4()
    application_id = uuid.uuid4()

    db_session.execute(
        text("INSERT INTO jobs (id) VALUES (CAST(:job_id AS uuid))"),
        {"job_id": str(job_id)},
    )
    db_session.execute(
        text(
            """
            INSERT INTO applications (id, job_id, state, automation_mode)
            VALUES (
                CAST(:application_id AS uuid),
                CAST(:job_id AS uuid),
                'ApplicationCreated',
                'manual'
            )
            """
        ),
        {"application_id": str(application_id), "job_id": str(job_id)},
    )

    invalid_writes = [
        (
            """
            INSERT INTO applications (id, job_id, state, automation_mode)
            VALUES (gen_random_uuid(), CAST(:job_id AS uuid), 'BadState', 'manual')
            """,
            {"job_id": str(job_id)},
        ),
        (
            """
            INSERT INTO applications (id, job_id, state, automation_mode)
            VALUES (
                gen_random_uuid(),
                CAST(:job_id AS uuid),
                'ApplicationCreated',
                'autopilot'
            )
            """,
            {"job_id": str(job_id)},
        ),
        (
            """
            INSERT INTO policy_decisions (
                id,
                application_id,
                action_type,
                mode,
                decision,
                allowed
            )
            VALUES (
                gen_random_uuid(),
                CAST(:application_id AS uuid),
                'submit',
                'autopilot',
                'review',
                false
            )
            """,
            {"application_id": str(application_id)},
        ),
        (
            """
            INSERT INTO policy_decisions (
                id,
                application_id,
                action_type,
                mode,
                decision,
                allowed
            )
            VALUES (
                gen_random_uuid(),
                CAST(:application_id AS uuid),
                'submit',
                'manual',
                'maybe',
                false
            )
            """,
            {"application_id": str(application_id)},
        ),
        (
            """
            INSERT INTO executor_actions (
                id,
                request_id,
                application_id,
                worker,
                idempotency_key,
                action_type,
                execution_mode,
                status,
                requested_by,
                requested_at
            )
            VALUES (
                gen_random_uuid(),
                gen_random_uuid(),
                CAST(:application_id AS uuid),
                'email',
                :idempotency_key,
                'submit',
                'simulate',
                'queued',
                'test',
                now()
            )
            """,
            {"application_id": str(application_id), "idempotency_key": "bad-mode"},
        ),
        (
            """
            INSERT INTO executor_actions (
                id,
                request_id,
                application_id,
                worker,
                idempotency_key,
                action_type,
                execution_mode,
                status,
                requested_by,
                requested_at
            )
            VALUES (
                gen_random_uuid(),
                gen_random_uuid(),
                CAST(:application_id AS uuid),
                'email',
                :idempotency_key,
                'submit',
                'dry_run',
                'mystery',
                'test',
                now()
            )
            """,
            {"application_id": str(application_id), "idempotency_key": "bad-status"},
        ),
        (
            """
            INSERT INTO executor_actions (
                id,
                request_id,
                application_id,
                worker,
                idempotency_key,
                action_type,
                execution_mode,
                status,
                requested_by,
                requested_at
            )
            VALUES (
                gen_random_uuid(),
                gen_random_uuid(),
                CAST(:application_id AS uuid),
                'calendar',
                :idempotency_key,
                'submit',
                'dry_run',
                'queued',
                'test',
                now()
            )
            """,
            {"application_id": str(application_id), "idempotency_key": "bad-worker"},
        ),
        (
            """
            INSERT INTO email_threads (id, application_id, direction)
            VALUES (gen_random_uuid(), CAST(:application_id AS uuid), 'sideways')
            """,
            {"application_id": str(application_id)},
        ),
    ]

    for statement, params in invalid_writes:
        with pytest.raises(IntegrityError):
            with db_session.begin_nested():
                db_session.execute(text(statement), params)


def test_audit_records_prevent_application_delete(db_session) -> None:
    """PostgreSQL prevents deleting applications with retained audit evidence."""

    def create_application() -> str:
        job_id = uuid.uuid4()
        application_id = uuid.uuid4()
        db_session.execute(
            text("INSERT INTO jobs (id) VALUES (CAST(:job_id AS uuid))"),
            {"job_id": str(job_id)},
        )
        db_session.execute(
            text(
                """
                INSERT INTO applications (id, job_id, state, automation_mode)
                VALUES (
                    CAST(:application_id AS uuid),
                    CAST(:job_id AS uuid),
                    'ApplicationCreated',
                    'manual'
                )
                """
            ),
            {"application_id": str(application_id), "job_id": str(job_id)},
        )
        return str(application_id)

    policy_application_id = create_application()
    db_session.execute(
        text(
            """
            INSERT INTO policy_decisions (
                id,
                application_id,
                action_type,
                mode,
                decision,
                allowed
            )
            VALUES (
                gen_random_uuid(),
                CAST(:application_id AS uuid),
                'submit',
                'dry_run',
                'allow',
                true
            )
            """
        ),
        {"application_id": policy_application_id},
    )

    executor_application_id = create_application()
    db_session.execute(
        text(
            """
            INSERT INTO executor_actions (
                id,
                request_id,
                application_id,
                worker,
                idempotency_key,
                action_type,
                execution_mode,
                status,
                requested_by,
                requested_at
            )
            VALUES (
                gen_random_uuid(),
                gen_random_uuid(),
                CAST(:application_id AS uuid),
                'email',
                :idempotency_key,
                'submit',
                'dry_run',
                'planned',
                'test',
                now()
            )
            """
        ),
        {
            "application_id": executor_application_id,
            "idempotency_key": "retention-executor-action",
        },
    )

    event_application_id = create_application()
    db_session.execute(
        text(
            """
            INSERT INTO event_log (id, application_id, event_type, actor)
            VALUES (
                gen_random_uuid(),
                CAST(:application_id AS uuid),
                'application.created',
                'test'
            )
            """
        ),
        {"application_id": event_application_id},
    )

    for application_id in (
        policy_application_id,
        executor_application_id,
        event_application_id,
    ):
        with pytest.raises(IntegrityError):
            with db_session.begin_nested():
                db_session.execute(
                    text(
                        """
                        DELETE FROM applications
                        WHERE id = CAST(:application_id AS uuid)
                        """
                    ),
                    {"application_id": application_id},
                )
