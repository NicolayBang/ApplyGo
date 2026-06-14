"""Unit tests for the side-effect-free executor stub."""

from applypilot.domain.executor import ExecutionMode, ExecutorRequest
from applypilot.services.executor_stub import StubExecutor


def test_dry_run_executor_returns_plan_without_side_effects() -> None:
    result = StubExecutor().dispatch(
        ExecutorRequest.create(
            action_type="send_follow_up_email",
            mode=ExecutionMode.DRY_RUN,
            application_id="application-001",
            worker="email",
            idempotency_key="dry-run-001",
            requested_by="user",
            payload={"policy_decision_id": "policy-001"},
        )
    )

    assert result.status == "planned"
    assert result.worker == "email"
    assert result.application_id == "application-001"
    assert result.details["execution_mode"] == "dry_run"
    assert result.details["side_effects"] is False
    assert result.details["request_id"] == str(result.request_id)
    assert result.details["worker"] == "email"
    assert result.details["requested_by"] == "user"
    assert result.details["policy_decision_id"] == "policy-001"
    assert result.details["requires"] == [
        "recorded_policy_decision",
        "stable_idempotency_key",
    ]
    assert "Validate recorded policy decision." in result.details["planned_steps"]
