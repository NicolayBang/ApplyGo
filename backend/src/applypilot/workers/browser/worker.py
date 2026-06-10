"""Placeholder browser worker implementation boundary."""

from applypilot.domain.executor.contracts import ExecutorRequest, ExecutorResult


class BrowserWorker:
    """Stub worker for future browser automation."""

    def run(self, request: ExecutorRequest) -> ExecutorResult:
        return ExecutorResult(status="not_implemented", details={"worker": "browser", "mode": request.mode})
