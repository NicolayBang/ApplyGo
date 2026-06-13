"""Top-level API router for milestone-1 scaffolding."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from applypilot.db.dependencies import TrackerUnitOfWork, get_tracker_unit
from applypilot.domain.executor import ExecutionMode, ExecutorRequest
from applypilot.domain.executor.schemas import ExecutorActionRead, ExecutorDryRunRequest
from applypilot.domain.applications.models import (
    ApplicationAuditRead,
    ApplicationCreate,
    ApplicationRead,
    ApplicationStateUpdate,
    EventLogRead,
    JobCreate,
    JobRead,
)
from applypilot.domain.policy import AutomationMode, PolicyContext, PolicyEngine, PolicyRequest
from applypilot.domain.policy.schemas import PolicyDecisionRead, PolicyEvaluationRequest
from applypilot.domain.state_machine import InvalidStateTransitionError
from applypilot.services.executor_stub import StubExecutor

router = APIRouter()
api_router = APIRouter()


@router.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    """Return a basic health response for local bootstrapping."""
    return {"status": "ok", "service": "applypilot"}


@router.post(
    "/jobs",
    response_model=JobRead,
    status_code=status.HTTP_201_CREATED,
    tags=["applications"],
)
def create_job(
    request: JobCreate,
    unit: TrackerUnitOfWork = Depends(get_tracker_unit),
) -> object:
    """Create a normalized job record."""
    job = unit.tracker.create_job(request)
    unit.commit()
    unit.refresh(job)
    return job


@router.post(
    "/applications",
    response_model=ApplicationRead,
    status_code=status.HTTP_201_CREATED,
    tags=["applications"],
)
def create_application(
    request: ApplicationCreate,
    unit: TrackerUnitOfWork = Depends(get_tracker_unit),
) -> object:
    """Create an application record and append the creation event."""
    if unit.tracker.get_job(request.job_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {request.job_id} not found",
        )

    application = unit.tracker.create_application(request)
    unit.commit()
    unit.refresh(application)
    return application


@router.get(
    "/applications",
    response_model=list[ApplicationRead],
    tags=["applications"],
)
def list_applications(
    state: str | None = None,
    limit: int = 50,
    offset: int = 0,
    unit: TrackerUnitOfWork = Depends(get_tracker_unit),
) -> list[object]:
    """List application records, optionally filtered by state."""
    return unit.tracker.list_applications(state=state, limit=limit, offset=offset)


@router.patch(
    "/applications/{application_id}/state",
    response_model=ApplicationRead,
    tags=["applications"],
)
def update_application_state(
    application_id: UUID,
    request: ApplicationStateUpdate,
    unit: TrackerUnitOfWork = Depends(get_tracker_unit),
) -> object:
    """Transition an application state through the state machine."""
    try:
        application = unit.tracker.update_state(
            application_id=application_id,
            new_state=request.state.value,
            actor=request.actor,
            payload=request.payload,
        )
    except InvalidStateTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    unit.commit()
    unit.refresh(application)
    return application


@router.post(
    "/applications/{application_id}/policy-decisions",
    response_model=PolicyDecisionRead,
    status_code=status.HTTP_201_CREATED,
    tags=["applications"],
)
def evaluate_application_policy(
    application_id: UUID,
    request: PolicyEvaluationRequest,
    unit: TrackerUnitOfWork = Depends(get_tracker_unit),
) -> object:
    """Evaluate and persist a policy decision before executor dispatch."""
    application = unit.tracker.get_application(application_id)
    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found",
        )

    try:
        mode = request.mode or AutomationMode(application.automation_mode)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown automation mode: {application.automation_mode}",
        ) from exc

    policy_request = PolicyRequest(
        application_id=application_id,
        current_state=application.state,
        requested_action=request.requested_action,
        worker=request.worker,
        context=PolicyContext(
            confidence=request.context.confidence,
            reasons=request.context.reasons,
            risks=request.context.risks,
            missing_data=request.context.missing_data,
            red_flags=request.context.red_flags,
        ),
        mode=mode,
    )
    decision = PolicyEngine().evaluate(policy_request)
    record = unit.tracker.record_policy_decision(
        request=policy_request,
        decision=decision,
        actor=request.actor,
    )
    unit.commit()
    unit.refresh(record)
    return record


@router.post(
    "/applications/{application_id}/executor-actions/dry-run",
    response_model=ExecutorActionRead,
    status_code=status.HTTP_201_CREATED,
    tags=["applications"],
)
def dry_run_executor_action(
    application_id: UUID,
    request: ExecutorDryRunRequest,
    unit: TrackerUnitOfWork = Depends(get_tracker_unit),
) -> object:
    """Plan an executor action without side effects and record audit events."""
    if unit.tracker.get_application(application_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found",
        )

    policy_decision = unit.tracker.get_policy_decision(request.policy_decision_id)
    if policy_decision is None or policy_decision.application_id != application_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A recorded policy decision is required before executor dry-run",
        )
    if not policy_decision.allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Policy decision {policy_decision.id} does not allow execution",
        )

    executor_request = ExecutorRequest(
        action_type=request.action_type,
        mode=ExecutionMode.DRY_RUN,
        application_id=str(application_id),
        idempotency_key=request.idempotency_key,
        payload={
            **request.payload,
            "policy_decision_id": str(request.policy_decision_id),
        },
    )
    result = StubExecutor().dispatch(executor_request)

    try:
        record = unit.tracker.record_executor_result(
            request=executor_request,
            result=result,
            actor=request.actor,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    unit.commit()
    unit.refresh(record)
    return record


@router.get(
    "/applications/{application_id}/events",
    response_model=list[EventLogRead],
    tags=["applications"],
)
def list_application_events(
    application_id: UUID,
    unit: TrackerUnitOfWork = Depends(get_tracker_unit),
) -> list[object]:
    """Return append-only events for an application."""
    if unit.tracker.get_application(application_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found",
        )

    return unit.tracker.get_events(application_id)


@router.get(
    "/applications/{application_id}/audit",
    response_model=ApplicationAuditRead,
    tags=["applications"],
)
def get_application_audit_summary(
    application_id: UUID,
    unit: TrackerUnitOfWork = Depends(get_tracker_unit),
) -> dict[str, object]:
    """Return the complete audit summary for one application."""
    application = unit.tracker.get_application(application_id)
    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found",
        )

    return {
        "application": application,
        "events": unit.tracker.get_events(application_id),
        "policy_decisions": unit.tracker.get_policy_decisions(application_id),
        "executor_actions": unit.tracker.get_executor_actions(application_id),
    }


api_router.include_router(router)
