"""Tracker repository - canonical application record CRUD.

This is the primary interface for creating and querying applications.
The state machine and event log call this to persist transitions.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from applypilot.db.models import Application, ApplicationPacketReview, EventLogEntry, ExecutorAction, Job
from applypilot.db.models import PolicyDecision as PolicyDecisionRecord
from applypilot.domain.applications.models import (
    ApplicationCreate,
    ApplicationPacketReviewCreate,
    JobCreate,
)
from applypilot.domain.applications.intake import JobIntakeClassifier
from applypilot.domain.applications.scoring import ApplicationScorer, JobScoringInput
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
        enriched = JobIntakeClassifier().enrich(data)
        job = Job(**enriched.model_dump())
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
        recommendation: str | None = None,
        company: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[Application]:
        query = self._session.query(Application)
        if state:
            query = query.filter(Application.state == state)
        if recommendation:
            query = query.filter(Application.recommendation == recommendation)
        if company:
            query = query.join(Application.job).filter(Job.company.ilike(f"%{company}%"))
        if created_from:
            query = query.filter(Application.created_at >= created_from)
        if created_to:
            query = query.filter(Application.created_at <= created_to)

        sort_columns = {
            "created_at": Application.created_at,
            "updated_at": Application.updated_at,
            "state": Application.state,
            "recommendation": Application.recommendation,
            "fit_score": Application.fit_score,
        }
        sort_column = sort_columns.get(sort_by)
        if sort_column is None:
            raise ValueError(f"Unsupported application sort field: {sort_by}")
        if sort_dir not in {"asc", "desc"}:
            raise ValueError(f"Unsupported application sort direction: {sort_dir}")

        order_by = asc(sort_column) if sort_dir == "asc" else desc(sort_column)
        return query.order_by(order_by).limit(limit).offset(offset).all()

    def update_state(
        self,
        application_id: uuid.UUID,
        new_state: str,
        actor: str = "system",
        payload: dict | None = None,
    ) -> Application:
        """Transition application state and append an event log entry."""
        target_state = self._parse_target_state(new_state)
        if target_state == ApplicationState.SUBMITTED:
            raise InvalidStateTransitionError(
                "Submitted state requires the submit_application workflow"
            )

        return self._transition_application_state(
            application_id=application_id,
            target_state=target_state,
            actor=actor,
            payload=payload,
        )

    def submit_application(
        self,
        application_id: uuid.UUID,
        actor: str = "system",
        payload: dict | None = None,
    ) -> Application:
        """Submit an approved application after verifying required audit evidence."""
        app = self._session.get(Application, application_id)
        if app is None:
            raise ValueError(f"Application {application_id} not found")

        old_state = self._current_state(app, application_id)
        self._state_machine.apply_transition(old_state, ApplicationState.SUBMITTED)
        self._ensure_submission_prerequisites(application_id)

        return self._transition_loaded_application_state(
            app=app,
            application_id=application_id,
            old_state=old_state,
            target_state=ApplicationState.SUBMITTED,
            actor=actor,
            payload=payload,
        )

    def _transition_application_state(
        self,
        *,
        application_id: uuid.UUID,
        target_state: ApplicationState,
        actor: str,
        payload: dict | None,
    ) -> Application:
        app = self._session.get(Application, application_id)
        if app is None:
            raise ValueError(f"Application {application_id} not found")

        old_state = self._current_state(app, application_id)

        self._state_machine.apply_transition(old_state, target_state)
        return self._transition_loaded_application_state(
            app=app,
            application_id=application_id,
            old_state=old_state,
            target_state=target_state,
            actor=actor,
            payload=payload,
        )

    def _transition_loaded_application_state(
        self,
        *,
        app: Application,
        application_id: uuid.UUID,
        old_state: ApplicationState,
        target_state: ApplicationState,
        actor: str,
        payload: dict | None,
    ) -> Application:
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

    def _current_state(
        self,
        app: Application,
        application_id: uuid.UUID,
    ) -> ApplicationState:
        try:
            return ApplicationState(app.state)
        except ValueError as exc:
            raise InvalidStateTransitionError(
                f"Application {application_id} has unknown state: {app.state}"
            ) from exc

    def _parse_target_state(self, new_state: str) -> ApplicationState:
        try:
            return ApplicationState(new_state)
        except ValueError as exc:
            raise InvalidStateTransitionError(f"Unknown target state: {new_state}") from exc

    def _ensure_submission_prerequisites(self, application_id: uuid.UUID) -> None:
        allowed_policy_ids = {
            str(decision.id)
            for decision in self.get_policy_decisions(application_id)
            if decision.allowed
        }
        if not allowed_policy_ids:
            raise InvalidStateTransitionError(
                "Submitted state requires an allowed policy decision"
            )

        has_executor_evidence = any(
            self._executor_matches_allowed_policy(action, allowed_policy_ids)
            for action in self.get_executor_actions(application_id)
        )
        if not has_executor_evidence:
            raise InvalidStateTransitionError(
                "Submitted state requires executor evidence for an allowed policy decision"
            )

    def _executor_matches_allowed_policy(
        self,
        action: ExecutorAction,
        allowed_policy_ids: set[str],
    ) -> bool:
        payload = action.payload or {}
        policy_decision_id = payload.get("policy_decision_id")
        if policy_decision_id not in allowed_policy_ids:
            return False

        return bool(action.result)

    def score_application(
        self,
        application_id: uuid.UUID,
        actor: str = "scoring",
    ) -> Application:
        """Calculate, persist, and audit deterministic application scoring."""
        app = self._session.get(Application, application_id)
        if app is None:
            raise ValueError(f"Application {application_id} not found")

        job = app.job
        result = ApplicationScorer().score(
            JobScoringInput(
                title=job.title,
                company=job.company,
                location=job.location,
                source_url=job.source_url,
                raw_text=job.raw_text,
                remote_ok=job.remote_ok,
                job_type=job.job_type,
                ats_type=job.ats_type,
                salary_raw=job.salary_raw,
            )
        )

        app.fit_score = result.fit_score
        app.confidence = result.confidence
        app.recommendation = result.recommendation
        app.score_reasons = result.reasons
        app.score_risks = result.risks
        app.missing_data = result.missing_data
        app.red_flags = result.red_flags
        app.updated_at = datetime.now(tz=timezone.utc)
        self._session.flush()

        self._append_event(
            application_id=application_id,
            event_type="application.scored",
            actor=actor,
            payload={
                "fit_score": result.fit_score,
                "confidence": result.confidence,
                "recommendation": result.recommendation,
                "reasons": result.reasons,
                "risks": result.risks,
                "missing_data": result.missing_data,
                "red_flags": result.red_flags,
            },
        )
        return app

    # ------------------------------------------------------------------
    # Packet reviews
    # ------------------------------------------------------------------

    def record_packet_review(
        self,
        application_id: uuid.UUID,
        data: ApplicationPacketReviewCreate,
    ) -> ApplicationPacketReview:
        """Persist human packet review evidence without side effects."""
        app = self._session.get(Application, application_id)
        if app is None:
            raise ValueError(f"Application {application_id} not found")

        review = ApplicationPacketReview(
            application_id=application_id,
            decision=data.decision,
            reviewed_by=data.reviewed_by,
            source=data.source,
            packet_text=data.packet_text,
            notes=data.notes,
        )
        self._session.add(review)
        self._session.flush()

        self._append_event(
            application_id=application_id,
            event_type="application_packet.reviewed",
            actor=data.reviewed_by,
            payload={
                "packet_review_id": str(review.id),
                "decision": review.decision,
                "reviewed_by": review.reviewed_by,
                "source": review.source,
                "notes_present": bool(review.notes),
                "packet_text_persisted": bool(review.packet_text),
            },
        )
        return review

    def get_packet_reviews(self, application_id: uuid.UUID) -> list[ApplicationPacketReview]:
        """Return packet reviews recorded for an application."""
        return (
            self._session.query(ApplicationPacketReview)
            .filter(ApplicationPacketReview.application_id == application_id)
            .order_by(ApplicationPacketReview.created_at.asc())
            .all()
        )

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

    def get_policy_decisions(self, application_id: uuid.UUID) -> list[PolicyDecisionRecord]:
        """Return policy decisions recorded for an application."""
        return (
            self._session.query(PolicyDecisionRecord)
            .filter(PolicyDecisionRecord.application_id == application_id)
            .order_by(PolicyDecisionRecord.created_at.asc())
            .all()
        )

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
        self._ensure_executor_result_matches_request(request, result)

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
            request_id=request.request_id,
            application_id=application_id,
            worker=request.worker,
            idempotency_key=request.idempotency_key,
            action_type=request.action_type,
            execution_mode=request.mode.value,
            status=result.status,
            requested_by=request.requested_by,
            requested_at=request.requested_at,
            payload=request.payload,
            result=result.details,
            completed_at=result.completed_at,
        )
        self._session.add(action)
        self._session.flush()

        self._append_event(
            application_id=application_id,
            event_type="executor_attempt_logged",
            actor=actor,
            payload={
                "executor_action_id": str(action.id),
                "request_id": str(action.request_id),
                "action_type": action.action_type,
                "worker": action.worker,
                "execution_mode": action.execution_mode,
                "idempotency_key": action.idempotency_key,
                "requested_by": action.requested_by,
                "requested_at": action.requested_at.isoformat(),
                "policy_decision_id": request.payload.get("policy_decision_id"),
            },
        )
        self._append_event(
            application_id=application_id,
            event_type="executor_result_logged",
            actor=actor,
            payload={
                "executor_action_id": str(action.id),
                "request_id": str(action.request_id),
                "status": action.status,
                "worker": action.worker,
                "result": action.result or {},
            },
        )
        return action

    def _ensure_executor_result_matches_request(
        self,
        request: ExecutorRequest,
        result: ExecutorResult,
    ) -> None:
        if result.request_id != request.request_id:
            raise ValueError("Executor result request_id does not match request")
        if result.application_id != request.application_id:
            raise ValueError("Executor result application_id does not match request")
        if result.worker != request.worker:
            raise ValueError("Executor result worker does not match request")
        if result.mode != request.mode:
            raise ValueError("Executor result mode does not match request")

    def get_executor_actions(self, application_id: uuid.UUID) -> list[ExecutorAction]:
        """Return executor actions recorded for an application."""
        return (
            self._session.query(ExecutorAction)
            .filter(ExecutorAction.application_id == application_id)
            .order_by(ExecutorAction.created_at.asc())
            .all()
        )

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
