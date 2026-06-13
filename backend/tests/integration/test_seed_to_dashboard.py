"""DB-backed integration test: seed → audit API (seed-to-dashboard flow).

Validates that seed_demo_application() creates persisted records in PostgreSQL
and that the /applications/{id}/audit endpoint returns a complete audit summary.

Requires PostgreSQL with migrations already applied (alembic upgrade head).
Skipped automatically at runtime when the database is unreachable.

Run explicitly:
    docker compose up -d postgres
    cd backend
    alembic upgrade head
    python -m pytest tests/integration/test_seed_to_dashboard.py -v
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text
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
    finally:
        app.dependency_overrides.pop(get_tracker_unit, None)
