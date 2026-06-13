"""Tracker repository - canonical application record CRUD.

This is the primary interface for creating and querying applications.
The state machine and event log call this to persist transitions.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from applypilot.db.models import Application, EventLogEntry, ExecutorAction, Job
from applypilot.db.models import PolicyDecision as PolicyDecisionRecord
from applypilot.domain.applications.models import ApplicationCreate, JobCreate
from applypilot.domain.executor import ExecutorRequest, ExecutorResult
from applypilot.domain.policy import PolicyDecision, PolicyRequest
from applypilot.domain.state_machine import (
    ApplicationState,
    ApplicationStateMachine,
    InvalidStateTransitionError,
)


class Tracker:
    """Canonical application record repository."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._state_machine = ApplicationStateMachine()

    # ------------------------------------------------------------------
    # Job
    # ------------------------------------------------------------------

    def create_job(self, data: JobCreate) -> Job:
        job = Job(**data.model_dump())
        self._session.add(job)
        self._session.flush()
        return job

    def get_job(self, job_id: uuid.UUID) -> Job | None:
        return self._session.get(Job, job_id)

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------

    def create_application(self, data: ApplicationCreate) -> Application:
        app = Application(
            job_id=data.job_id,
            automation_mode=data.automation_mode,
            state=ApplicationState.APPLICATION_CREATED.value,
        )
        self._session.add(app)
        self._session.flush()
        self._append_event(
            application_id=app.id,
            event_type="application.created",
            actor="system",
            to_state=ApplicationState.APPLICATION_CREATED.value,
            payload={"automation_mode": data.automation_mode},
        )
        return app

    def get_application(self, application_id: uuid.UUID) -> Application | None:
        return self._session.get(Application, application_id)

    def list_applications(
        self,
        state: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Application]:
        query = self._session.query(Application)
        if state:
            query = query.filter(Application.state == state)
        return query.order_by(Application.created_at.desc()).limit(limit).offset(offset).all()

    def update_state(
        self,
        application_id: uuid.UUID,
        new_state: str,
        actor: str = "system",
        payload: dict | None = None,
    ) -> Application:
        """Transition application state and append an event log entry."""
        app = self._session.get(Application, application_id)
        if app is None:
            raise ValueError(f"Application {application_id} not found")

        try:
            old_state = ApplicationState(app.state)
        except ValueError as exc:
            raise InvalidStateTransitionError(
                f"Application {application_id} has unknown state: {app.state}"
            ) from exc

        try:
            target_state = ApplicationState(new_state)
        except ValueError as exc:
            raise InvalidStateTransitionError(f"Unknown target state: {new_state}") from exc

        self._state_machine.apply_transition(old_state, target_state)

        app.state = target_state.value
        app.updated_at = datetime.now(tz=timezone.utc)
        self._session.flush()

        self._append_event(
            application_id=application_id,
            event_type="application.state_changed",
            actor=actor,
            from_state=old_state.value,
            to_state=target_state.value,
            payload=payload,
        )
        return app

    # ------------------------------------------------------------------
    # Policy decisions
    # ------------------------------------------------------------------

    def record_policy_decision(
        self,
        request: PolicyRequest,
        decision: PolicyDecision,
        actor: str = "policy",
    ) -> PolicyDecisionRecord:
        """Persist a policy decision and append the required audit event."""
        app = self._session.get(Application, request.application_id)
        if app is None:
            raise ValueError(f"Application {request.application_id} not found")

        record = PolicyDecisionRecord(
            id=decision.decision_id,
            application_id=request.application_id,
            action_type=request.requested_action,
            mode=decision.mode.value,
            decision=decision.decision.value,
            allowed=decision.allowed,
            reasons=decision.reasons,
            risks=request.context.risks,
            required_overrides=decision.required_overrides,
        )
        self._session.add(record)
        self._session.flush()

        self._append_event(
            application_id=request.application_id,
            event_type="policy_decision_logged",
            actor=actor,
            payload={
                "decision_id": str(record.id),
                "action_type": record.action_type,
                "worker": request.worker.value,
                "mode": record.mode,
                "decision": record.decision,
                "allowed": record.allowed,
                "reasons": record.reasons or [],
                "risks": record.risks or [],
                "required_overrides": record.required_overrides or [],
            },
        )
        return record

    def get_policy_decision(
        self,
        policy_decision_id: uuid.UUID,
    ) -> PolicyDecisionRecord | None:
        """Return a previously recorded policy decision."""
        return self._session.get(PolicyDecisionRecord, policy_decision_id)

    # ------------------------------------------------------------------
    # Executor actions
    # ------------------------------------------------------------------

    def record_executor_result(
        self,
        request: ExecutorRequest,
        result: ExecutorResult,
        actor: str = "worker",
    ) -> ExecutorAction:
        """Persist a dry-run executor action and append attempt/result audit events."""
        application_id = uuid.UUID(request.application_id)
        app = self._session.get(Application, application_id)
        if app is None:
            raise ValueError(f"Application {application_id} not found")

        existing = (
            self._session.query(ExecutorAction)
            .filter(ExecutorAction.idempotency_key == request.idempotency_key)
            .one_or_none()
        )
        if existing is not None:
            if existing.application_id != application_id:
                raise ValueError(
                    f"Idempotency key {request.idempotency_key} belongs to another application"
                )
            return existing

        action = ExecutorAction(
            application_id=application_id,
            idempotency_key=request.idempotency_key,
            action_type=request.action_type,
            execution_mode=request.mode.value,
            status=result.status,
            payload=request.payload,
            result=result.details,
            completed_at=datetime.now(tz=timezone.utc),
        )
        self._session.add(action)
        self._session.flush()

        self._append_event(
            application_id=application_id,
            event_type="executor_attempt_logged",
            actor=actor,
            payload={
                "executor_action_id": str(action.id),
                "action_type": action.action_type,
                "execution_mode": action.execution_mode,
                "idempotency_key": action.idempotency_key,
                "policy_decision_id": request.payload.get("policy_decision_id"),
            },
        )
        self._append_event(
            application_id=application_id,
            event_type="executor_result_logged",
            actor=actor,
            payload={
                "executor_action_id": str(action.id),
                "status": action.status,
                "result": action.result or {},
            },
        )
        return action

    # ------------------------------------------------------------------
    # Event log (append-only)
    # ------------------------------------------------------------------

    def _append_event(
        self,
        *,
        application_id: uuid.UUID,
        event_type: str,
        actor: str = "system",
        from_state: str | None = None,
        to_state: str | None = None,
        payload: dict | None = None,
    ) -> EventLogEntry:
        entry = EventLogEntry(
            application_id=application_id,
            event_type=event_type,
            actor=actor,
            from_state=from_state,
            to_state=to_state,
            payload=payload or {},
        )
        self._session.add(entry)
        self._session.flush()
        return entry

    def get_events(self, application_id: uuid.UUID) -> list[EventLogEntry]:
        return (
            self._session.query(EventLogEntry)
            .filter(EventLogEntry.application_id == application_id)
            .order_by(EventLogEntry.created_at.asc())
            .all()
        )
