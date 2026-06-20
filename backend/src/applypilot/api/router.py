"""Top-level API router for milestone-1 scaffolding."""

from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from applypilot.db.dependencies import TrackerUnitOfWork, get_tracker_unit
from applypilot.db.tracker import (
    M5ConflictError,
    M5Error,
    M5NotFoundError,
)
from applypilot.domain.executor import ExecutionMode, ExecutorRequest
from applypilot.domain.executor.schemas import ExecutorActionRead, ExecutorDryRunRequest
from applypilot.domain.applications.models import (
    AnswerCreate,
    AnswerRead,
    AnswerUpdate,
    ApplicationAnswerCreate,
    ApplicationAnswerRead,
    ApplicationAuditRead,
    ApplicationCreate,
    ApplicationDocumentCreate,
    ApplicationDocumentRead,
    ApplicationPacketRead,
    ApplicationPacketReviewCreate,
    ApplicationPacketReviewRead,
    ApplicationRead,
    ApplicationReviewSummaryRead,
    ApplicationScoreRequest,
    ApplicationStateUpdate,
    DocumentCreate,
    DocumentRead,
    DocumentVersionCreate,
    DocumentVersionRead,
    EventLogRead,
    JobCreate,
    JobRead,
)
from applypilot.domain.policy import (
    AutomationMode,
    ConfidenceLevel,
    PolicyContext,
    PolicyEngine,
    PolicyRequest,
)
from applypilot.domain.policy.schemas import PolicyDecisionRead, PolicyEvaluationRequest
from applypilot.domain.state_machine import ApplicationState, InvalidStateTransitionError
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
    recommendation: str | None = None,
    company: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
    limit: int = 50,
    offset: int = 0,
    unit: TrackerUnitOfWork = Depends(get_tracker_unit),
) -> list[object]:
    """List application records with lightweight tracker filters."""
    try:
        return unit.tracker.list_applications(
            state=state,
            recommendation=recommendation,
            company=company,
            created_from=created_from,
            created_to=created_to,
            sort_by=sort_by,
            sort_dir=sort_dir,
            limit=limit,
            offset=offset,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


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
        if request.state == ApplicationState.SUBMITTED:
            application = unit.tracker.submit_application(
                application_id=application_id,
                actor=request.actor,
                payload=request.payload,
            )
        else:
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
    "/applications/{application_id}/score",
    response_model=ApplicationRead,
    tags=["applications"],
)
def score_application(
    application_id: UUID,
    request: ApplicationScoreRequest | None = None,
    unit: TrackerUnitOfWork = Depends(get_tracker_unit),
) -> object:
    """Record deterministic application scoring for downstream policy checks."""
    try:
        application = unit.tracker.score_application(
            application_id=application_id,
            actor=request.actor if request else "scoring",
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    unit.commit()
    unit.refresh(application)
    return application


@router.post(
    "/applications/{application_id}/packet-reviews",
    response_model=ApplicationPacketReviewRead,
    status_code=status.HTTP_201_CREATED,
    tags=["applications"],
)
def create_application_packet_review(
    application_id: UUID,
    request: ApplicationPacketReviewCreate,
    unit: TrackerUnitOfWork = Depends(get_tracker_unit),
) -> object:
    """Record a human packet review decision without external side effects."""
    try:
        review = unit.tracker.record_packet_review(
            application_id=application_id,
            data=request,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    unit.commit()
    unit.refresh(review)
    return review


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

    context = _policy_context(request, application)
    policy_request = PolicyRequest(
        application_id=application_id,
        current_state=application.state,
        requested_action=request.requested_action,
        worker=request.worker,
        context=context,
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


def _policy_context(request: PolicyEvaluationRequest, application: object) -> PolicyContext:
    if request.context is not None:
        return PolicyContext(
            confidence=request.context.confidence,
            fit_score=request.context.fit_score,
            recommendation=request.context.recommendation,
            reasons=request.context.reasons,
            risks=request.context.risks,
            missing_data=request.context.missing_data,
            red_flags=request.context.red_flags,
        )

    confidence = getattr(application, "confidence", None) or ConfidenceLevel.LOW.value
    try:
        confidence_level = ConfidenceLevel(confidence)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown stored confidence level: {confidence}",
        ) from exc

    missing_data = list(getattr(application, "missing_data", None) or [])
    if getattr(application, "fit_score", None) is None:
        missing_data.append("application score")

    return PolicyContext(
        confidence=confidence_level,
        fit_score=getattr(application, "fit_score", None),
        recommendation=getattr(application, "recommendation", None),
        reasons=list(getattr(application, "score_reasons", None) or []),
        risks=list(getattr(application, "score_risks", None) or []),
        missing_data=missing_data,
        red_flags=list(getattr(application, "red_flags", None) or []),
    )


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

    executor_request = ExecutorRequest.create(
        action_type=request.action_type,
        mode=ExecutionMode.DRY_RUN,
        application_id=str(application_id),
        worker=request.worker,
        idempotency_key=request.idempotency_key,
        requested_by=request.actor,
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


@router.get(
    "/applications/{application_id}/review-summary",
    response_model=ApplicationReviewSummaryRead,
    tags=["applications"],
)
def get_application_review_summary(
    application_id: UUID,
    unit: TrackerUnitOfWork = Depends(get_tracker_unit),
) -> dict[str, object]:
    """Return a compact reviewer-facing application summary."""
    application = unit.tracker.get_application(application_id)
    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found",
        )

    policy_decisions = unit.tracker.get_policy_decisions(application_id)
    executor_actions = unit.tracker.get_executor_actions(application_id)
    packet_reviews = unit.tracker.get_packet_reviews(application_id)
    events = unit.tracker.get_events(application_id)
    latest_policy_decision = policy_decisions[-1] if policy_decisions else None
    latest_executor_action = executor_actions[-1] if executor_actions else None
    latest_packet_review = packet_reviews[-1] if packet_reviews else None
    allowed_policy_ids = {
        str(decision.id)
        for decision in policy_decisions
        if decision.allowed
    }
    has_submission_evidence = any(
        (action.payload or {}).get("policy_decision_id") in allowed_policy_ids
        and bool(action.result)
        for action in executor_actions
    )

    return {
        "application": application,
        "latest_policy_decision": latest_policy_decision,
        "latest_executor_action": latest_executor_action,
        "latest_packet_review": latest_packet_review,
        "packet_reviews": packet_reviews,
        "event_count": len(events),
        "next_states": _next_states(application.state, has_submission_evidence),
        "ready_for_policy": bool(application.confidence),
        "ready_for_dry_run": bool(latest_policy_decision and latest_policy_decision.allowed),
        "ready_for_submission": (
            application.state == ApplicationState.APPROVED.value and has_submission_evidence
        ),
    }


def _next_states(state_value: str, has_submission_evidence: bool) -> list[str]:
    transitions = {
        ApplicationState.APPLICATION_CREATED.value: [ApplicationState.DRAFT.value],
        ApplicationState.DRAFT.value: [
            ApplicationState.READY_FOR_REVIEW.value,
            ApplicationState.ARCHIVED.value,
        ],
        ApplicationState.READY_FOR_REVIEW.value: [
            ApplicationState.APPROVED.value,
            ApplicationState.REJECTED.value,
            ApplicationState.DRAFT.value,
        ],
        ApplicationState.APPROVED.value: [
            ApplicationState.SUBMITTED.value,
            ApplicationState.REJECTED.value,
        ],
        ApplicationState.SUBMITTED.value: [ApplicationState.ARCHIVED.value],
        ApplicationState.REJECTED.value: [ApplicationState.ARCHIVED.value],
        ApplicationState.ARCHIVED.value: [],
    }
    next_states = transitions.get(state_value, [])
    if state_value == ApplicationState.APPROVED.value and not has_submission_evidence:
        return [state for state in next_states if state != ApplicationState.SUBMITTED.value]
    return next_states


# ---------------------------------------------------------------------------
# M5 document/answer/packet routes
# ---------------------------------------------------------------------------

def _m5_http_error(exc: M5Error) -> HTTPException:
    """Map an M5 contract error to its HTTP status (404 / 409 / 400)."""
    if isinstance(exc, M5NotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, M5ConflictError):
        status_code = status.HTTP_409_CONFLICT
    else:
        status_code = status.HTTP_400_BAD_REQUEST
    return HTTPException(status_code=status_code, detail=str(exc))


@router.post(
    "/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
    tags=["documents"],
)
def create_document(
    request: DocumentCreate,
    unit: TrackerUnitOfWork = Depends(get_tracker_unit),
) -> object:
    """Create a reusable logical document."""
    try:
        document = unit.tracker.create_document(
            doc_type=request.doc_type, name=request.name
        )
    except M5Error as exc:
        raise _m5_http_error(exc) from exc

    unit.commit()
    unit.refresh(document)
    return document


@router.get("/documents", response_model=list[DocumentRead], tags=["documents"])
def list_documents(
    unit: TrackerUnitOfWork = Depends(get_tracker_unit),
) -> list[object]:
    """List non-archived logical documents in deterministic order."""
    return unit.tracker.list_documents()


@router.get(
    "/documents/{document_id}",
    response_model=DocumentRead,
    tags=["documents"],
)
def get_document(
    document_id: UUID,
    unit: TrackerUnitOfWork = Depends(get_tracker_unit),
) -> object:
    """Read one logical document by ID (including archived)."""
    try:
        return unit.tracker.get_document(document_id)
    except M5Error as exc:
        raise _m5_http_error(exc) from exc


@router.post(
    "/documents/{document_id}/archive",
    response_model=DocumentRead,
    tags=["documents"],
)
def archive_document(
    document_id: UUID,
    unit: TrackerUnitOfWork = Depends(get_tracker_unit),
) -> object:
    """Idempotently archive a logical document."""
    try:
        document = unit.tracker.archive_document(document_id)
    except M5Error as exc:
        raise _m5_http_error(exc) from exc

    unit.commit()
    unit.refresh(document)
    return document


@router.post(
    "/documents/{document_id}/versions",
    response_model=DocumentVersionRead,
    status_code=status.HTTP_201_CREATED,
    tags=["documents"],
)
def add_document_version(
    document_id: UUID,
    request: DocumentVersionCreate,
    unit: TrackerUnitOfWork = Depends(get_tracker_unit),
) -> object:
    """Append an immutable version to a logical document."""
    try:
        version = unit.tracker.add_document_version(
            document_id,
            content=request.content,
            content_json=request.content_json,
        )
    except M5Error as exc:
        raise _m5_http_error(exc) from exc

    unit.commit()
    unit.refresh(version)
    return version


@router.get(
    "/documents/{document_id}/versions",
    response_model=list[DocumentVersionRead],
    tags=["documents"],
)
def list_document_versions(
    document_id: UUID,
    unit: TrackerUnitOfWork = Depends(get_tracker_unit),
) -> list[object]:
    """List a document's immutable versions in ascending version order."""
    try:
        return unit.tracker.list_document_versions(document_id)
    except M5Error as exc:
        raise _m5_http_error(exc) from exc


@router.get(
    "/document-versions/{version_id}",
    response_model=DocumentVersionRead,
    tags=["documents"],
)
def get_document_version(
    version_id: UUID,
    unit: TrackerUnitOfWork = Depends(get_tracker_unit),
) -> object:
    """Read one immutable document version by ID."""
    try:
        return unit.tracker.get_document_version(version_id)
    except M5Error as exc:
        raise _m5_http_error(exc) from exc


@router.post(
    "/answers",
    response_model=AnswerRead,
    status_code=status.HTTP_201_CREATED,
    tags=["answers"],
)
def create_answer(
    request: AnswerCreate,
    unit: TrackerUnitOfWork = Depends(get_tracker_unit),
) -> object:
    """Create a reusable library answer."""
    try:
        answer = unit.tracker.create_answer(
            question_key=request.question_key,
            question_text=request.question_text,
            answer_text=request.answer_text,
        )
    except M5Error as exc:
        raise _m5_http_error(exc) from exc

    unit.commit()
    unit.refresh(answer)
    return answer


@router.get("/answers", response_model=list[AnswerRead], tags=["answers"])
def list_answers(
    unit: TrackerUnitOfWork = Depends(get_tracker_unit),
) -> list[object]:
    """List non-archived library answers ordered by question_key, then id."""
    return unit.tracker.list_answers()


@router.get("/answers/{answer_id}", response_model=AnswerRead, tags=["answers"])
def get_answer(
    answer_id: UUID,
    unit: TrackerUnitOfWork = Depends(get_tracker_unit),
) -> object:
    """Read one library answer by ID (including archived)."""
    try:
        return unit.tracker.get_answer(answer_id)
    except M5Error as exc:
        raise _m5_http_error(exc) from exc


@router.patch("/answers/{answer_id}", response_model=AnswerRead, tags=["answers"])
def update_answer(
    answer_id: UUID,
    request: AnswerUpdate,
    unit: TrackerUnitOfWork = Depends(get_tracker_unit),
) -> object:
    """Edit a library answer's current text in place (never the question_key)."""
    try:
        answer = unit.tracker.update_answer(
            answer_id,
            question_text=request.question_text,
            answer_text=request.answer_text,
        )
    except M5Error as exc:
        raise _m5_http_error(exc) from exc

    unit.commit()
    unit.refresh(answer)
    return answer


@router.post(
    "/answers/{answer_id}/archive",
    response_model=AnswerRead,
    tags=["answers"],
)
def archive_answer(
    answer_id: UUID,
    unit: TrackerUnitOfWork = Depends(get_tracker_unit),
) -> object:
    """Idempotently archive a library answer."""
    try:
        answer = unit.tracker.archive_answer(answer_id)
    except M5Error as exc:
        raise _m5_http_error(exc) from exc

    unit.commit()
    unit.refresh(answer)
    return answer


@router.post(
    "/applications/{application_id}/documents",
    response_model=ApplicationDocumentRead,
    status_code=status.HTTP_201_CREATED,
    tags=["applications"],
)
def attach_application_document(
    application_id: UUID,
    request: ApplicationDocumentCreate,
    unit: TrackerUnitOfWork = Depends(get_tracker_unit),
) -> object:
    """Attach one exact document version to an application (append-only)."""
    try:
        attachment = unit.tracker.attach_document(
            application_id,
            document_version_id=request.document_version_id,
            role=request.role,
            display_order=request.display_order,
            actor=request.actor,
        )
    except M5Error as exc:
        raise _m5_http_error(exc) from exc

    unit.commit()
    unit.refresh(attachment)
    return attachment


@router.get(
    "/applications/{application_id}/documents",
    response_model=list[ApplicationDocumentRead],
    tags=["applications"],
)
def list_application_documents(
    application_id: UUID,
    unit: TrackerUnitOfWork = Depends(get_tracker_unit),
) -> list[object]:
    """List an application's document attachments in deterministic order."""
    try:
        return unit.tracker.list_application_documents(application_id)
    except M5Error as exc:
        raise _m5_http_error(exc) from exc


@router.post(
    "/applications/{application_id}/answers",
    response_model=ApplicationAnswerRead,
    status_code=status.HTTP_201_CREATED,
    tags=["applications"],
)
def record_application_answer(
    application_id: UUID,
    request: ApplicationAnswerCreate,
    unit: TrackerUnitOfWork = Depends(get_tracker_unit),
) -> object:
    """Record an immutable answer snapshot (sourced from the library or manual)."""
    try:
        snapshot = unit.tracker.record_application_answer(
            application_id,
            answer_library_id=request.answer_library_id,
            question_key=request.question_key,
            question_text=request.question_text,
            answer_text=request.answer_text,
            actor=request.actor,
        )
    except M5Error as exc:
        raise _m5_http_error(exc) from exc

    unit.commit()
    unit.refresh(snapshot)
    return snapshot


@router.get(
    "/applications/{application_id}/answers",
    response_model=list[ApplicationAnswerRead],
    tags=["applications"],
)
def list_application_answers(
    application_id: UUID,
    unit: TrackerUnitOfWork = Depends(get_tracker_unit),
) -> list[object]:
    """List an application's immutable answer snapshots ordered by created_at, id."""
    try:
        return unit.tracker.list_application_answers(application_id)
    except M5Error as exc:
        raise _m5_http_error(exc) from exc


@router.get(
    "/applications/{application_id}/packet",
    response_model=ApplicationPacketRead,
    tags=["applications"],
)
def get_application_packet(
    application_id: UUID,
    unit: TrackerUnitOfWork = Depends(get_tracker_unit),
) -> dict[str, object]:
    """Return the application packet read model (documents, answers, latest M2 review)."""
    try:
        return unit.tracker.get_packet(application_id)
    except M5Error as exc:
        raise _m5_http_error(exc) from exc


api_router.include_router(router)
