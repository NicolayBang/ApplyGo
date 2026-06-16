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
from applypilot.db.models import Company
from applypilot.domain.applications.models import JobCreate

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


def test_m3_tracker_create_job_resolves_company_identity(db_session) -> None:
    """New job writes preserve display text and populate the M3 company identity FK."""
    from applypilot.db.tracker import Tracker

    tracker = Tracker(db_session)

    first = tracker.create_job(
        JobCreate(title="Backend Engineer", company="  ApplyPilot,   Inc. ")
    )
    second = tracker.create_job(
        JobCreate(title="Frontend Engineer", company="applypilot inc")
    )
    unknown = tracker.create_job(JobCreate(title="Mystery Role"))
    confidential = tracker.create_job(
        JobCreate(title="Platform Role", company="Confidential employer")
    )

    assert first.company == "ApplyPilot, Inc."
    assert first.company_id == second.company_id
    assert unknown.company is None
    assert unknown.company_id is not None
    assert confidential.company == "Confidential employer"
    assert confidential.company_id is not None

    companies = {
        company.name: company
        for company in db_session.query(Company).order_by(Company.name).all()
    }
    assert companies["ApplyPilot, Inc."].normalized_name == "applypilot inc"
    assert companies["ApplyPilot, Inc."].normalized_domain is None
    assert companies["Unknown Company"].normalized_name == "unknown company"
    assert companies["Confidential Company"].normalized_name == "confidential company"


def test_m3_tracker_create_job_does_not_infer_company_domain_from_source_url(
    db_session,
) -> None:
    """Job source URLs may identify ATS hosts, not employer domains."""
    from applypilot.db.tracker import Tracker

    tracker = Tracker(db_session)

    job = tracker.create_job(
        JobCreate(
            title="Data Engineer",
            company="Example Co",
            source_url="https://jobs.lever.co/not-the-employer/data-engineer",
        )
    )

    company = db_session.get(Company, job.company_id)
    assert company is not None
    assert company.name == "Example Co"
    assert company.normalized_name == "example co"
    assert company.domain is None
    assert company.normalized_domain is None


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


def test_m2_packet_review_constraints_allow_nullable_packet_text(db_session) -> None:
    """PostgreSQL accepts valid packet reviews without storing packet text."""
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
    db_session.execute(
        text(
            """
            INSERT INTO application_packet_reviews (
                id,
                application_id,
                decision,
                reviewed_by,
                source,
                packet_text,
                notes
            )
            VALUES (
                gen_random_uuid(),
                CAST(:application_id AS uuid),
                'approved',
                'human',
                'dashboard',
                NULL,
                :notes
            )
            """
        ),
        {"application_id": str(application_id), "notes": "Looks ready for manual use."},
    )

    row = db_session.execute(
        text(
            """
            SELECT decision, reviewed_by, source, packet_text, notes
            FROM application_packet_reviews
            WHERE application_id = CAST(:application_id AS uuid)
            """
        ),
        {"application_id": str(application_id)},
    ).one()

    assert row.decision == "approved"
    assert row.reviewed_by == "human"
    assert row.source == "dashboard"
    assert row.packet_text is None
    assert row.notes == "Looks ready for manual use."


def test_m2_packet_review_constraints_reject_invalid_values(db_session) -> None:
    """PostgreSQL rejects packet review decisions outside the M2 contract."""
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
            INSERT INTO application_packet_reviews (
                id,
                application_id,
                decision,
                reviewed_by,
                source
            )
            VALUES (
                gen_random_uuid(),
                CAST(:application_id AS uuid),
                'maybe',
                'human',
                'dashboard'
            )
            """,
            {"application_id": str(application_id)},
        ),
        (
            """
            INSERT INTO application_packet_reviews (
                id,
                application_id,
                decision,
                reviewed_by,
                source
            )
            VALUES (
                gen_random_uuid(),
                CAST(:application_id AS uuid),
                'approved',
                'human',
                'browser'
            )
            """,
            {"application_id": str(application_id)},
        ),
    ]

    for statement, params in invalid_writes:
        with pytest.raises(IntegrityError):
            with db_session.begin_nested():
                db_session.execute(text(statement), params)


def test_m2_packet_review_tracker_appends_audit_event(db_session) -> None:
    """Tracker writes packet review evidence and the audit event in one unit of work."""
    from applypilot.db.tracker import Tracker
    from applypilot.domain.applications.models import ApplicationPacketReviewCreate

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

    tracker = Tracker(db_session)
    review = tracker.record_packet_review(
        application_id,
        ApplicationPacketReviewCreate(
            decision="approved",
            reviewed_by="human",
            source="dashboard",
            packet_text="Generated packet text should not be copied into the event.",
            notes="Reviewed for manual use.",
        ),
    )
    events = tracker.get_events(application_id)

    assert review.application_id == application_id
    assert review.packet_text == "Generated packet text should not be copied into the event."
    assert [event.event_type for event in events] == ["application_packet.reviewed"]
    event = events[0]
    assert event.actor == "human"
    assert event.payload == {
        "packet_review_id": str(review.id),
        "decision": "approved",
        "reviewed_by": "human",
        "source": "dashboard",
        "notes_present": True,
        "packet_text_persisted": True,
    }
    assert "packet_text" not in event.payload


def test_m2_packet_review_api_updates_summary_and_timeline(db_session) -> None:
    """API path records packet review evidence visible to dashboard read models."""
    from fastapi.testclient import TestClient

    from applypilot.db.dependencies import TrackerUnitOfWork, get_tracker_unit
    from applypilot.main import app

    def override_tracker_unit():
        yield TrackerUnitOfWork(db_session)

    app.dependency_overrides[get_tracker_unit] = override_tracker_unit
    try:
        client = TestClient(app)
        job_response = client.post(
            "/jobs",
            json={
                "title": "Packet Review Engineer",
                "company": "ApplyPilot Test Co.",
                "location": "Remote",
                "raw_text": "Build reviewed application packets with audit-safe workflows.",
            },
        )
        assert job_response.status_code == 201

        application_response = client.post(
            "/applications",
            json={
                "job_id": job_response.json()["id"],
                "automation_mode": "manual",
            },
        )
        assert application_response.status_code == 201
        application_id = application_response.json()["id"]

        packet_review_response = client.post(
            f"/applications/{application_id}/packet-reviews",
            json={
                "decision": "changes_requested",
                "reviewed_by": "human",
                "source": "dashboard",
                "notes": "Clarify one requirement before manual use.",
            },
        )
        assert packet_review_response.status_code == 201
        packet_review = packet_review_response.json()

        summary_response = client.get(f"/applications/{application_id}/review-summary")
        assert summary_response.status_code == 200
        summary = summary_response.json()
        assert summary["latest_packet_review"]["id"] == packet_review["id"]
        assert summary["latest_packet_review"]["decision"] == "changes_requested"
        assert summary["latest_packet_review"]["notes"] == "Clarify one requirement before manual use."

        events_response = client.get(f"/applications/{application_id}/events")
        assert events_response.status_code == 200
        event = events_response.json()[-1]
        assert event["event_type"] == "application_packet.reviewed"
        assert event["payload"]["packet_review_id"] == packet_review["id"]
        assert event["payload"]["decision"] == "changes_requested"
        assert "packet_text" not in event["payload"]
    finally:
        app.dependency_overrides.pop(get_tracker_unit, None)


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

    packet_review_application_id = create_application()
    db_session.execute(
        text(
            """
            INSERT INTO application_packet_reviews (
                id,
                application_id,
                decision,
                reviewed_by,
                source
            )
            VALUES (
                gen_random_uuid(),
                CAST(:application_id AS uuid),
                'approved',
                'human',
                'dashboard'
            )
            """
        ),
        {"application_id": packet_review_application_id},
    )

    for application_id in (
        policy_application_id,
        executor_application_id,
        event_application_id,
        packet_review_application_id,
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
