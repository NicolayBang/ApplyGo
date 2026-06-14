"""Placeholder email worker implementation boundary."""

from applypilot.domain.executor.contracts import ExecutorRequest, ExecutorResult


class EmailWorker:
    """Stub worker for future Gmail integration."""

    def run(self, request: ExecutorRequest) -> ExecutorResult:
        return ExecutorResult(
            request_id=request.request_id,
            application_id=request.application_id,
            worker=request.worker,
            mode=request.mode,
            status="not_implemented",
            details={"worker": "email", "mode": request.mode.value},
        )
