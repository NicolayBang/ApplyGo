"""Unit tests for the side-effect-free executor stub."""

from applypilot.domain.executor import ExecutionMode, ExecutorRequest
from applypilot.services.executor_stub import StubExecutor


def test_dry_run_executor_returns_plan_without_side_effects() -> None:
    result = StubExecutor().dispatch(
        ExecutorRequest(
            action_type="send_follow_up_email",
            mode=ExecutionMode.DRY_RUN,
            application_id="application-001",
            idempotency_key="dry-run-001",
            payload={"policy_decision_id": "policy-001"},
        )
    )

    assert result.status == "planned"
    assert result.details["execution_mode"] == "dry_run"
    assert result.details["side_effects"] is False
    assert result.details["policy_decision_id"] == "policy-001"
    assert result.details["requires"] == [
        "recorded_policy_decision",
        "stable_idempotency_key",
    ]
    assert "Validate recorded policy decision." in result.details["planned_steps"]
