#!/usr/bin/env python
"""Validate the seed-to-dashboard flow against a live PostgreSQL database.

This script is intended for Codespaces or any environment with PostgreSQL running.
It exercises the full stack: migrations → demo_seed → audit API endpoint.

Prerequisites:
    docker compose up -d postgres
    cd backend
    pip install -e ".[dev]"
    alembic upgrade head

Usage:
    python -m scripts.validate_seed_to_dashboard

Expected output:
    - Demo seed creates an application with audit records.
    - The /applications/{id}/audit endpoint returns a complete audit summary.
    - The /applications/{id}/review-summary endpoint returns reviewer readiness.
    - All assertions pass and the script exits 0.
"""

from __future__ import annotations

import sys

from fastapi.testclient import TestClient


def main() -> int:
    from applypilot.db.dependencies import TrackerUnitOfWork, get_tracker_unit
    from applypilot.db.session import SessionLocal
    from applypilot.db.tracker import Tracker
    from applypilot.dev.demo_seed import seed_demo_application
    from applypilot.main import app

    print("=" * 60)
    print("Seed-to-Dashboard Validation Script")
    print("=" * 60)

    # --- Step 1: Seed demo data ---
    print("\n[1/3] Running seed_demo_application against PostgreSQL...")
    session = SessionLocal()
    try:
        tracker = Tracker(session)
        result = seed_demo_application(tracker)
        session.commit()
    except Exception as exc:
        session.rollback()
        print(f"  FAIL: seed_demo_application raised: {exc}")
        return 1
    finally:
        session.close()

    print(f"  Application ID: {result.application_id}")
    print(f"  Policy Decision ID: {result.policy_decision_id}")
    print(f"  Executor Action ID: {result.executor_action_id}")

    # --- Step 2: Verify via Tracker queries ---
    print("\n[2/3] Verifying persisted records via Tracker...")
    session = SessionLocal()
    try:
        tracker = Tracker(session)

        application = tracker.get_application(result.application_id)
        assert application is not None, "Application not found in DB"
        assert application.state == "ApplicationCreated"
        print(f"  Application state: {application.state} ✓")

        events = tracker.get_events(result.application_id)
        event_types = [e.event_type for e in events]
        assert "application.created" in event_types, "Missing application.created event"
        assert "policy_decision_logged" in event_types, "Missing policy_decision_logged event"
        assert "executor_attempt_logged" in event_types, "Missing executor_attempt_logged event"
        assert "executor_result_logged" in event_types, "Missing executor_result_logged event"
        print(f"  Events ({len(events)}): {event_types} ✓")

        policy_decisions = tracker.get_policy_decisions(result.application_id)
        assert len(policy_decisions) == 1, "Expected 1 policy decision"
        assert policy_decisions[0].allowed is True, "Policy decision should be allowed"
        print(f"  Policy decision: allowed={policy_decisions[0].allowed} ✓")

        executor_actions = tracker.get_executor_actions(result.application_id)
        assert len(executor_actions) == 1, "Expected 1 executor action"
        assert executor_actions[0].status == "planned", "Executor status should be 'planned'"
        assert executor_actions[0].execution_mode == "dry_run"
        print(f"  Executor action: status={executor_actions[0].status}, mode=dry_run ✓")
    finally:
        session.close()

    # --- Step 3: Verify via dashboard API endpoints ---
    print("\n[3/3] Verifying dashboard API endpoints...")
    session = SessionLocal()
    try:
        def override_tracker_unit():
            yield TrackerUnitOfWork(session)

        app.dependency_overrides[get_tracker_unit] = override_tracker_unit
        client = TestClient(app)
        response = client.get(f"/applications/{result.application_id}/audit")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        body = response.json()

        assert body["application"]["id"] == str(result.application_id)
        assert body["application"]["state"] == "ApplicationCreated"
        print(f"  Audit API returned application: {body['application']['id']} ✓")

        api_event_types = [e["event_type"] for e in body["events"]]
        assert "application.created" in api_event_types
        assert "policy_decision_logged" in api_event_types
        assert "executor_attempt_logged" in api_event_types
        assert "executor_result_logged" in api_event_types
        print(f"  Audit API events: {api_event_types} ✓")

        assert len(body["policy_decisions"]) == 1
        assert body["policy_decisions"][0]["allowed"] is True
        print("  Audit API policy decisions: 1 (allowed=True) ✓")

        assert len(body["executor_actions"]) == 1
        assert body["executor_actions"][0]["status"] == "planned"
        assert body["executor_actions"][0]["execution_mode"] == "dry_run"
        review_response = client.get(f"/applications/{result.application_id}/review-summary")
        assert review_response.status_code == 200, (
            f"Expected 200, got {review_response.status_code}"
        )
        review_body = review_response.json()
        assert review_body["application"]["id"] == str(result.application_id)
        assert review_body["event_count"] >= 4
        assert review_body["latest_policy_decision"]["id"] == str(result.policy_decision_id)
        assert review_body["latest_policy_decision"]["allowed"] is True
        assert review_body["latest_executor_action"]["id"] == str(result.executor_action_id)
        assert review_body["latest_executor_action"]["status"] == "planned"
        assert review_body["ready_for_dry_run"] is True
        assert review_body["ready_for_submission"] is False
        assert review_body["next_states"] == ["Draft"]
        print("  Audit API executor actions: 1 (planned, dry_run) ✓")
    finally:
        app.dependency_overrides.pop(get_tracker_unit, None)
        session.close()

    print("\n" + "=" * 60)
    print("ALL VALIDATIONS PASSED ✓")
    print("=" * 60)
    print(f"\nDashboard API: GET /applications/{result.application_id}/audit")
    print(f"Review API: GET /applications/{result.application_id}/review-summary")
    return 0


if __name__ == "__main__":
    sys.exit(main())
