"""Dry-run friendly executor stub for milestone 1."""

from applypilot.domain.executor.contracts import ExecutorRequest, ExecutorResult


class StubExecutor:
    """Simulate outbound actions without side effects."""

    def dispatch(self, request: ExecutorRequest) -> ExecutorResult:
        is_dry_run = request.mode.value == "dry_run"
        return ExecutorResult(
            status="planned" if is_dry_run else "queued",
            details={
                "action_type": request.action_type,
                "application_id": request.application_id,
                "idempotency_key": request.idempotency_key,
                "execution_mode": request.mode.value,
                "side_effects": not is_dry_run,
                "requires": [
                    "recorded_policy_decision",
                    "stable_idempotency_key",
                ],
                "planned_steps": [
                    "Validate recorded policy decision.",
                    f"Prepare {request.action_type} payload.",
                    "Record executor result in the audit trail.",
                ],
                "policy_decision_id": request.payload.get("policy_decision_id"),
            },
        )
