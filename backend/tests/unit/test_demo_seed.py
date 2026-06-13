"""Tests for the development demo seed workflow."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

from applypilot.dev.demo_seed import seed_demo_application
from applypilot.domain.executor import ExecutionMode
from applypilot.domain.policy import AutomationMode


class FakeTracker:
    """Tracker double that records seed workflow ordering."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.created_application = None
        self.policy_request = None
        self.executor_request = None
        self.job = SimpleNamespace(id=uuid.uuid4())
        self.application = SimpleNamespace(
            id=uuid.uuid4(),
            state="ApplicationCreated",
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        self.policy_record = SimpleNamespace(id=uuid.uuid4())
        self.executor_action = SimpleNamespace(id=uuid.uuid4())

    def create_job(self, data):
        self.calls.append("create_job")
        self.created_job = data
        return self.job

    def create_application(self, data):
        self.calls.append("create_application")
        self.created_application = data
        return self.application

    def record_policy_decision(self, request, decision, actor="policy"):
        self.calls.append("record_policy_decision")
        self.policy_request = request
        self.policy_decision = decision
        self.policy_actor = actor
        return self.policy_record

    def record_executor_result(self, request, result, actor="worker"):
        self.calls.append("record_executor_result")
        self.executor_request = request
        self.executor_result = result
        self.executor_actor = actor
        return self.executor_action


class FakeExecutor:
    """Executor double that captures the dispatched request."""

    def __init__(self) -> None:
        self.dispatched_request = None

    def dispatch(self, request):
        self.dispatched_request = request
        return SimpleNamespace(status="planned", details={"idempotency_key": request.idempotency_key})


def test_demo_seed_creates_application_policy_and_dry_run_executor_audit_records() -> None:
    tracker = FakeTracker()
    executor = FakeExecutor()

    result = seed_demo_application(tracker, executor=executor)

    assert result.job_id == tracker.job.id
    assert result.application_id == tracker.application.id
    assert result.policy_decision_id == tracker.policy_record.id
    assert result.executor_action_id == tracker.executor_action.id
    assert tracker.created_application.job_id == tracker.job.id
    assert tracker.created_application.automation_mode == AutomationMode.MANUAL.value
    assert tracker.policy_request.application_id == tracker.application.id
    assert tracker.policy_request.mode == AutomationMode.DRY_RUN
    assert tracker.policy_decision.allowed is True
    assert tracker.executor_request.mode == ExecutionMode.DRY_RUN
    assert tracker.executor_request.payload["policy_decision_id"] == str(tracker.policy_record.id)
    assert tracker.executor_request.idempotency_key == f"demo-seed-{tracker.application.id}"
    assert executor.dispatched_request == tracker.executor_request
    assert tracker.calls == [
        "create_job",
        "create_application",
        "record_policy_decision",
        "record_executor_result",
    ]
