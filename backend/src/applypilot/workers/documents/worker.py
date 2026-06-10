"""Placeholder document worker implementation boundary."""

from applypilot.domain.executor.contracts import ExecutorRequest, ExecutorResult


class DocumentWorker:
    """Stub worker for future document generation."""

    def run(self, request: ExecutorRequest) -> ExecutorResult:
        return ExecutorResult(status="not_implemented", details={"worker": "documents", "mode": request.mode})
