"""Unit tests for executor request/result contract enforcement."""

import pytest

from applypilot.db.tracker import Tracker
from applypilot.domain.executor import ExecutionMode, ExecutorRequest, ExecutorResult


def test_tracker_rejects_executor_result_with_mismatched_request_id() -> None:
    request = ExecutorRequest.create(
        action_type="send_follow_up_email",
        mode=ExecutionMode.DRY_RUN,
        application_id="00000000-0000-0000-0000-000000000001",
        worker="email",
        idempotency_key="dry-run-001",
    )
    result = ExecutorResult(
        request_id=ExecutorRequest.create(
            action_type="send_follow_up_email",
            mode=ExecutionMode.DRY_RUN,
            application_id=request.application_id,
            worker=request.worker,
            idempotency_key="dry-run-002",
        ).request_id,
        application_id=request.application_id,
        worker=request.worker,
        mode=request.mode,
        status="planned",
    )

    with pytest.raises(ValueError, match="request_id"):
        Tracker(None)._ensure_executor_result_matches_request(request, result)  # type: ignore[arg-type]


def test_tracker_rejects_executor_result_with_mismatched_worker() -> None:
    request = ExecutorRequest.create(
        action_type="send_follow_up_email",
        mode=ExecutionMode.DRY_RUN,
        application_id="00000000-0000-0000-0000-000000000001",
        worker="email",
        idempotency_key="dry-run-001",
    )
    result = ExecutorResult(
        request_id=request.request_id,
        application_id=request.application_id,
        worker="browser",
        mode=request.mode,
        status="planned",
    )

    with pytest.raises(ValueError, match="worker"):
        Tracker(None)._ensure_executor_result_matches_request(request, result)  # type: ignore[arg-type]


def test_tracker_accepts_executor_result_matching_request_metadata() -> None:
    request = ExecutorRequest.create(
        action_type="send_follow_up_email",
        mode=ExecutionMode.DRY_RUN,
        application_id="00000000-0000-0000-0000-000000000001",
        worker="email",
        idempotency_key="dry-run-001",
    )
    result = ExecutorResult(
        request_id=request.request_id,
        application_id=request.application_id,
        worker=request.worker,
        mode=request.mode,
        status="planned",
    )

    Tracker(None)._ensure_executor_result_matches_request(request, result)  # type: ignore[arg-type]
