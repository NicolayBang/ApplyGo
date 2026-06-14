"""API tests for the M1 application workflow spine."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

from applypilot.db.dependencies import get_tracker_unit
from applypilot.domain.state_machine import InvalidStateTransitionError
from applypilot.main import app


class FakeTracker:
    """Small in-memory tracker double for API behavior tests."""

    def __init__(self) -> None:
        self.job_id = uuid.uuid4()
        self.application_id = uuid.uuid4()
        self.created_at = datetime.now(tz=UTC)
        self.job = SimpleNamespace(
            id=self.job_id,
            source_url="https://example.com/jobs/backend-developer",
            raw_text=(
                "Build Python API services with FastAPI, PostgreSQL, automation, "
                "and platform data workflows for a remote team."
            ),
            title="Backend Developer",
            company="ApplyPilot",
            location="Remote",
            remote_ok=True,
            job_type="full-time",
            ats_type="lever",
            salary_raw="$95,000 - $125,000",
            created_at=self.created_at,
            updated_at=self.created_at,
        )
        self.application = SimpleNamespace(
            id=self.application_id,
            job_id=self.job_id,
            job=self.job,
            state="ApplicationCreated",
            automation_mode="manual",
            fit_score=None,
            confidence=None,
            recommendation=None,
            score_reasons=None,
            score_risks=None,
            missing_data=None,
            red_flags=None,
            created_at=self.created_at,
            updated_at=self.created_at,
        )
        self.events = [
            SimpleNamespace(
                id=uuid.uuid4(),
                application_id=self.application_id,
                event_type="application.created",
                actor="system",
                from_state=None,
                to_state="ApplicationCreated",
                payload={"automation_mode": "manual"},
                created_at=self.created_at,
            )
        ]
        self.policy_decisions = []
        self.executor_actions = []

    def create_job(self, data):
        self.job.title = data.title
        self.job.company = data.company
        self.job.location = data.location
        self.job.source_url = data.source_url
        self.job.raw_text = data.raw_text
        self.job.remote_ok = data.remote_ok
        self.job.job_type = data.job_type
        self.job.ats_type = data.ats_type
        self.job.salary_raw = data.salary_raw
        return self.job

    def get_job(self, job_id):
        return self.job if job_id == self.job_id else None

    def create_application(self, data):
        self.application.job_id = data.job_id
        self.application.automation_mode = data.automation_mode
        return self.application

    def get_application(self, application_id):
        return self.application if application_id == self.application_id else None

    def list_applications(self, state=None, limit=50, offset=0):
        applications = [self.application]
        if state is not None:
            applications = [item for item in applications if item.state == state]
        return applications[offset : offset + limit]

    def update_state(self, application_id, new_state, actor="system", payload=None):
        if application_id != self.application_id:
            raise ValueError(f"Application {application_id} not found")
        if self.application.state == "ApplicationCreated" and new_state == "Submitted":
            raise InvalidStateTransitionError("Invalid transition: ApplicationCreated -> Submitted")

        old_state = self.application.state
        self.application.state = new_state
        self.events.append(
            SimpleNamespace(
                id=uuid.uuid4(),
                application_id=self.application_id,
                event_type="application.state_changed",
                actor=actor,
                from_state=old_state,
                to_state=new_state,
                payload=payload or {},
                created_at=datetime.now(tz=UTC),
            )
        )
        return self.application

    def score_application(self, application_id, actor="scoring"):
        if application_id != self.application_id:
            raise ValueError(f"Application {application_id} not found")

        self.application.fit_score = 87
        self.application.confidence = "high"
        self.application.recommendation = "recommended"
        self.application.score_reasons = [
            "Role title is available for review.",
            "Relevant technical keywords were found.",
        ]
        self.application.score_risks = []
        self.application.missing_data = []
        self.application.red_flags = []
        self.application.updated_at = datetime.now(tz=UTC)
        self.events.append(
            SimpleNamespace(
                id=uuid.uuid4(),
                application_id=self.application_id,
                event_type="application.scored",
                actor=actor,
                from_state=None,
                to_state=None,
                payload={
                    "fit_score": self.application.fit_score,
                    "confidence": self.application.confidence,
                    "recommendation": self.application.recommendation,
                    "reasons": self.application.score_reasons,
                    "risks": self.application.score_risks,
                    "missing_data": self.application.missing_data,
                    "red_flags": self.application.red_flags,
                },
                created_at=datetime.now(tz=UTC),
            )
        )
        return self.application

    def record_policy_decision(self, request, decision, actor="policy"):
        if request.application_id != self.application_id:
            raise ValueError(f"Application {request.application_id} not found")

        record = SimpleNamespace(
            id=decision.decision_id,
            application_id=request.application_id,
            action_type=request.requested_action,
            mode=decision.mode.value,
            decision=decision.decision.value,
            allowed=decision.allowed,
            reasons=decision.reasons,
            risks=request.context.risks,
            required_overrides=decision.required_overrides,
            created_at=decision.created_at,
        )
        self.policy_decisions.append(record)
        self.events.append(
            SimpleNamespace(
                id=uuid.uuid4(),
                application_id=self.application_id,
                event_type="policy_decision_logged",
                actor=actor,
                from_state=None,
                to_state=None,
                payload={
                    "decision_id": str(record.id),
                    "action_type": record.action_type,
                    "worker": request.worker.value,
                    "mode": record.mode,
                    "decision": record.decision,
                    "allowed": record.allowed,
                    "reasons": record.reasons,
                    "risks": record.risks,
                    "required_overrides": record.required_overrides,
                },
                created_at=datetime.now(tz=UTC),
            )
        )
        return record

    def get_policy_decision(self, policy_decision_id):
        for decision in self.policy_decisions:
            if decision.id == policy_decision_id:
                return decision
        return None

    def get_policy_decisions(self, application_id):
        if application_id != self.application_id:
            return []
        return self.policy_decisions

    def record_executor_result(self, request, result, actor="worker"):
        application_id = uuid.UUID(request.application_id)
        if application_id != self.application_id:
            raise ValueError(f"Application {application_id} not found")

        for action in self.executor_actions:
            if action.idempotency_key == request.idempotency_key:
                return action

        record = SimpleNamespace(
            id=uuid.uuid4(),
            application_id=application_id,
            idempotency_key=request.idempotency_key,
            action_type=request.action_type,
            execution_mode=request.mode.value,
            status=result.status,
            payload=request.payload,
            result=result.details,
            created_at=datetime.now(tz=UTC),
            completed_at=datetime.now(tz=UTC),
        )
        self.executor_actions.append(record)
        self.events.append(
            SimpleNamespace(
                id=uuid.uuid4(),
                application_id=self.application_id,
                event_type="executor_attempt_logged",
                actor=actor,
                from_state=None,
                to_state=None,
                payload={
                    "executor_action_id": str(record.id),
                    "action_type": record.action_type,
                    "execution_mode": record.execution_mode,
                    "idempotency_key": record.idempotency_key,
                    "policy_decision_id": request.payload.get("policy_decision_id"),
                },
                created_at=datetime.now(tz=UTC),
            )
        )
        self.events.append(
            SimpleNamespace(
                id=uuid.uuid4(),
                application_id=self.application_id,
                event_type="executor_result_logged",
                actor=actor,
                from_state=None,
                to_state=None,
                payload={
                    "executor_action_id": str(record.id),
                    "status": record.status,
                    "result": record.result,
                },
                created_at=datetime.now(tz=UTC),
            )
        )
        return record

    def get_executor_actions(self, application_id):
        if application_id != self.application_id:
            return []
        return self.executor_actions

    def get_events(self, application_id):
        if application_id != self.application_id:
            return []
        return self.events


class FakeUnitOfWork:
    def __init__(self, tracker: FakeTracker) -> None:
        self.tracker = tracker

    def commit(self) -> None:
        return None

    def refresh(self, instance: object) -> None:
        return None


def make_client(tracker: FakeTracker) -> TestClient:
    def override_tracker_unit():
        yield FakeUnitOfWork(tracker)

    app.dependency_overrides[get_tracker_unit] = override_tracker_unit
    return TestClient(app)


def test_create_job_returns_created_job() -> None:
    tracker = FakeTracker()
    client = make_client(tracker)

    response = client.post(
        "/jobs",
        json={
            "title": "Backend Developer",
            "company": "ApplyPilot",
            "location": "Remote",
            "source_url": "https://example.com/jobs/backend-developer",
            "raw_text": "Build reliable backend APIs with Python, FastAPI, and PostgreSQL.",
            "remote_ok": True,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Backend Developer"
    assert body["company"] == "ApplyPilot"
    assert body["source_url"] == "https://example.com/jobs/backend-developer"
    assert body["raw_text"] == "Build reliable backend APIs with Python, FastAPI, and PostgreSQL."


def test_application_flow_creates_lists_transitions_and_returns_events() -> None:
    tracker = FakeTracker()
    client = make_client(tracker)

    create_response = client.post(
        "/applications",
        json={"job_id": str(tracker.job_id), "automation_mode": "manual"},
    )
    assert create_response.status_code == 201
    assert create_response.json()["state"] == "ApplicationCreated"

    list_response = client.get("/applications")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    transition_response = client.patch(
        f"/applications/{tracker.application_id}/state",
        json={"state": "Draft", "actor": "user", "payload": {"reason": "manual intake"}},
    )
    assert transition_response.status_code == 200
    assert transition_response.json()["state"] == "Draft"

    events_response = client.get(f"/applications/{tracker.application_id}/events")
    assert events_response.status_code == 200
    events = events_response.json()
    assert [event["event_type"] for event in events] == [
        "application.created",
        "application.state_changed",
    ]
    assert events[1]["from_state"] == "ApplicationCreated"
    assert events[1]["to_state"] == "Draft"


def test_create_application_returns_404_when_job_missing() -> None:
    tracker = FakeTracker()
    client = make_client(tracker)

    response = client.post(
        "/applications",
        json={"job_id": str(uuid.uuid4()), "automation_mode": "manual"},
    )

    assert response.status_code == 404


def test_invalid_state_transition_returns_400() -> None:
    tracker = FakeTracker()
    client = make_client(tracker)

    response = client.patch(
        f"/applications/{tracker.application_id}/state",
        json={"state": "Submitted"},
    )

    assert response.status_code == 400
    assert "Invalid transition" in response.json()["detail"]


def test_application_score_is_persisted_and_audited() -> None:
    tracker = FakeTracker()
    client = make_client(tracker)

    response = client.post(
        f"/applications/{tracker.application_id}/score",
        json={"actor": "user"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["fit_score"] == 87
    assert body["confidence"] == "high"
    assert body["recommendation"] == "recommended"

    events_response = client.get(f"/applications/{tracker.application_id}/events")
    assert events_response.status_code == 200
    events = events_response.json()
    assert events[-1]["event_type"] == "application.scored"
    assert events[-1]["actor"] == "user"
    assert events[-1]["payload"]["fit_score"] == 87


def test_application_score_returns_404_when_application_missing() -> None:
    tracker = FakeTracker()
    client = make_client(tracker)

    response = client.post(f"/applications/{uuid.uuid4()}/score")

    assert response.status_code == 404


def test_policy_decision_is_evaluated_persisted_and_audited() -> None:
    tracker = FakeTracker()
    client = make_client(tracker)

    response = client.post(
        f"/applications/{tracker.application_id}/policy-decisions",
        json={
            "requested_action": "send_follow_up_email",
            "worker": "email",
            "mode": "full_auto",
            "context": {
                "confidence": "low",
                "reasons": ["incomplete recruiter context"],
                "risks": [],
                "missing_data": [],
                "red_flags": [],
            },
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["decision"] == "review"
    assert body["allowed"] is False
    assert body["required_overrides"] == ["human_review"]

    events_response = client.get(f"/applications/{tracker.application_id}/events")
    assert events_response.status_code == 200
    events = events_response.json()
    assert events[-1]["event_type"] == "policy_decision_logged"
    assert events[-1]["actor"] == "policy"
    assert events[-1]["payload"]["decision"] == "review"


def test_policy_decision_uses_stored_application_score_when_context_is_omitted() -> None:
    tracker = FakeTracker()
    client = make_client(tracker)
    score_response = client.post(f"/applications/{tracker.application_id}/score")
    assert score_response.status_code == 200

    response = client.post(
        f"/applications/{tracker.application_id}/policy-decisions",
        json={
            "requested_action": "send_follow_up_email",
            "worker": "email",
            "mode": "dry_run",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["decision"] == "allow"
    assert body["allowed"] is True
    assert tracker.policy_decisions[0].risks == []


def test_policy_decision_returns_404_when_application_missing() -> None:
    tracker = FakeTracker()
    client = make_client(tracker)

    response = client.post(
        f"/applications/{uuid.uuid4()}/policy-decisions",
        json={
            "requested_action": "send_follow_up_email",
            "worker": "email",
            "context": {"confidence": "high"},
        },
    )

    assert response.status_code == 404


def test_executor_dry_run_is_persisted_and_audited() -> None:
    tracker = FakeTracker()
    client = make_client(tracker)
    policy_response = client.post(
        f"/applications/{tracker.application_id}/policy-decisions",
        json={
            "requested_action": "send_follow_up_email",
            "worker": "email",
            "mode": "dry_run",
            "context": {"confidence": "high"},
        },
    )

    response = client.post(
        f"/applications/{tracker.application_id}/executor-actions/dry-run",
        json={
            "policy_decision_id": policy_response.json()["id"],
            "action_type": "send_follow_up_email",
            "idempotency_key": "dry-run-001",
            "payload": {"template": "follow_up"},
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["action_type"] == "send_follow_up_email"
    assert body["execution_mode"] == "dry_run"
    assert body["status"] == "planned"
    assert body["result"]["idempotency_key"] == "dry-run-001"

    events_response = client.get(f"/applications/{tracker.application_id}/events")
    assert events_response.status_code == 200
    events = events_response.json()
    assert [event["event_type"] for event in events[-2:]] == [
        "executor_attempt_logged",
        "executor_result_logged",
    ]
    assert events[-2]["payload"]["idempotency_key"] == "dry-run-001"
    assert events[-2]["payload"]["policy_decision_id"] == policy_response.json()["id"]
    assert events[-1]["payload"]["status"] == "planned"


def test_executor_dry_run_reuses_idempotent_result() -> None:
    tracker = FakeTracker()
    client = make_client(tracker)
    policy_response = client.post(
        f"/applications/{tracker.application_id}/policy-decisions",
        json={
            "requested_action": "send_follow_up_email",
            "worker": "email",
            "mode": "dry_run",
            "context": {"confidence": "high"},
        },
    )
    payload = {
        "policy_decision_id": policy_response.json()["id"],
        "action_type": "send_follow_up_email",
        "idempotency_key": "dry-run-001",
        "payload": {"template": "follow_up"},
    }

    first_response = client.post(
        f"/applications/{tracker.application_id}/executor-actions/dry-run",
        json=payload,
    )
    event_count = len(tracker.events)
    second_response = client.post(
        f"/applications/{tracker.application_id}/executor-actions/dry-run",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert second_response.json()["id"] == first_response.json()["id"]
    assert len(tracker.executor_actions) == 1
    assert len(tracker.events) == event_count


def test_executor_dry_run_returns_404_when_application_missing() -> None:
    tracker = FakeTracker()
    client = make_client(tracker)

    response = client.post(
        f"/applications/{uuid.uuid4()}/executor-actions/dry-run",
        json={
            "policy_decision_id": uuid.uuid4().hex,
            "action_type": "send_follow_up_email",
            "idempotency_key": "dry-run-001",
        },
    )

    assert response.status_code == 404


def test_executor_dry_run_requires_recorded_policy_decision() -> None:
    tracker = FakeTracker()
    client = make_client(tracker)

    response = client.post(
        f"/applications/{tracker.application_id}/executor-actions/dry-run",
        json={
            "policy_decision_id": str(uuid.uuid4()),
            "action_type": "send_follow_up_email",
            "idempotency_key": "dry-run-001",
        },
    )

    assert response.status_code == 400
    assert "policy decision is required" in response.json()["detail"]


def test_application_audit_summary_returns_application_events_policy_and_executor_records() -> None:
    tracker = FakeTracker()
    client = make_client(tracker)

    policy_response = client.post(
        f"/applications/{tracker.application_id}/policy-decisions",
        json={
            "requested_action": "send_follow_up_email",
            "worker": "email",
            "mode": "dry_run",
            "context": {"confidence": "high"},
        },
    )
    executor_response = client.post(
        f"/applications/{tracker.application_id}/executor-actions/dry-run",
        json={
            "policy_decision_id": policy_response.json()["id"],
            "action_type": "send_follow_up_email",
            "idempotency_key": "dry-run-001",
        },
    )

    response = client.get(f"/applications/{tracker.application_id}/audit")

    assert response.status_code == 200
    body = response.json()
    assert body["application"]["id"] == str(tracker.application_id)
    assert body["application"]["job"]["job_type"] == "full-time"
    assert body["application"]["job"]["ats_type"] == "lever"
    assert [event["event_type"] for event in body["events"]] == [
        "application.created",
        "policy_decision_logged",
        "executor_attempt_logged",
        "executor_result_logged",
    ]
    assert body["policy_decisions"][0]["id"] == policy_response.json()["id"]
    assert body["policy_decisions"][0]["allowed"] is True
    assert body["executor_actions"][0]["id"] == executor_response.json()["id"]
    assert body["executor_actions"][0]["status"] == "planned"


def test_application_audit_summary_returns_404_when_application_missing() -> None:
    tracker = FakeTracker()
    client = make_client(tracker)

    response = client.get(f"/applications/{uuid.uuid4()}/audit")

    assert response.status_code == 404
