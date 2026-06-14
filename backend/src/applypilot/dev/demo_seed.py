"""Seed a demo audit trail for local dashboard review."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from applypilot.db.session import SessionLocal
from applypilot.db.tracker import Tracker
from applypilot.domain.applications.models import ApplicationCreate, JobCreate
from applypilot.domain.executor import ExecutionMode, ExecutorRequest
from applypilot.domain.policy import (
    AutomationMode,
    ConfidenceLevel,
    PolicyContext,
    PolicyEngine,
    PolicyRequest,
    WorkerType,
)
from applypilot.services.executor_stub import StubExecutor


@dataclass(frozen=True, slots=True)
class DemoSeedResult:
    """Identifiers created by the demo seed workflow."""

    job_id: UUID
    application_id: UUID
    policy_decision_id: UUID
    executor_action_id: UUID


def seed_demo_application(
    tracker: Tracker,
    *,
    executor: StubExecutor | None = None,
) -> DemoSeedResult:
    """Create one demo application with policy and executor audit records."""
    job = tracker.create_job(
        JobCreate(
            source_url="https://example.com/jobs/applypilot-platform-engineer",
            raw_text=(
                "Platform Engineer role focused on reliable automation, "
                "auditability, and human-in-the-loop workflows."
            ),
            title="Platform Engineer",
            company="ApplyPilot Demo Co.",
            location="Remote",
            remote_ok=True,
            job_type="Full-time",
            ats_type="demo",
            salary_raw="$95,000 - $125,000",
        )
    )
    application = tracker.create_application(
        ApplicationCreate(job_id=job.id, automation_mode=AutomationMode.MANUAL.value)
    )

    policy_request = PolicyRequest(
        application_id=application.id,
        current_state=application.state,
        requested_action="send_follow_up_email",
        worker=WorkerType.EMAIL,
        context=PolicyContext(
            confidence=ConfidenceLevel.HIGH,
            reasons=["Demo profile has enough information for a dry-run follow-up."],
        ),
        mode=AutomationMode.DRY_RUN,
    )
    policy_decision = PolicyEngine().evaluate(policy_request)
    if not policy_decision.allowed:
        raise RuntimeError("Demo seed policy decision unexpectedly blocked executor dry-run.")

    policy_record = tracker.record_policy_decision(policy_request, policy_decision)
    executor_request = ExecutorRequest.create(
        action_type=policy_request.requested_action,
        mode=ExecutionMode.DRY_RUN,
        application_id=str(application.id),
        worker=policy_request.worker.value,
        idempotency_key=f"demo-seed-{application.id}",
        requested_by="demo_seed",
        payload={
            "policy_decision_id": str(policy_record.id),
            "template": "demo_follow_up",
        },
    )
    executor_result = (executor or StubExecutor()).dispatch(executor_request)
    executor_action = tracker.record_executor_result(executor_request, executor_result)

    return DemoSeedResult(
        job_id=job.id,
        application_id=application.id,
        policy_decision_id=policy_record.id,
        executor_action_id=executor_action.id,
    )


def main() -> None:
    """Run the demo seed workflow against the configured database."""
    session = SessionLocal()
    try:
        result = seed_demo_application(Tracker(session))
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    print("Demo audit data created.")
    print(f"Job ID: {result.job_id}")
    print(f"Application ID: {result.application_id}")
    print(f"Policy decision ID: {result.policy_decision_id}")
    print(f"Executor action ID: {result.executor_action_id}")
    print(f"Dashboard API: /applications/{result.application_id}/audit")


if __name__ == "__main__":
    main()
