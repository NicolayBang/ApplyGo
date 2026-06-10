"""Dry-run friendly executor stub for milestone 1."""

from applypilot.domain.executor.contracts import ExecutorRequest, ExecutorResult


class StubExecutor:
    """Simulate outbound actions without side effects."""

    def dispatch(self, request: ExecutorRequest) -> ExecutorResult:
        return ExecutorResult(
            status="planned" if request.mode.value == "dry_run" else "queued",
            details={
                "action_type": request.action_type,
                "application_id": request.application_id,
                "idempotency_key": request.idempotency_key,
            },
        )
