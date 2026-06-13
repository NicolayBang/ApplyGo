"""Top-level API router for milestone-1 scaffolding."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from applypilot.db.dependencies import TrackerUnitOfWork, get_tracker_unit
from applypilot.domain.applications.models import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationStateUpdate,
    EventLogRead,
    JobCreate,
    JobRead,
)
from applypilot.domain.state_machine import InvalidStateTransitionError

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


api_router.include_router(router)
