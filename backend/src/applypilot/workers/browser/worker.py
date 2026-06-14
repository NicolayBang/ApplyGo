"""Placeholder browser worker implementation boundary."""

from applypilot.domain.executor.contracts import ExecutorRequest, ExecutorResult


class BrowserWorker:
    """Stub worker for future browser automation."""

    def run(self, request: ExecutorRequest) -> ExecutorResult:
        return ExecutorResult(
            request_id=request.request_id,
            application_id=request.application_id,
            worker=request.worker,
            mode=request.mode,
            status="not_implemented",
            details={"worker": "browser", "mode": request.mode.value},
        )
