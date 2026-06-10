"""Placeholder email worker implementation boundary."""

from applypilot.domain.executor.contracts import ExecutorRequest, ExecutorResult


class EmailWorker:
    """Stub worker for future Gmail integration."""

    def run(self, request: ExecutorRequest) -> ExecutorResult:
        return ExecutorResult(status="not_implemented", details={"worker": "email", "mode": request.mode})
