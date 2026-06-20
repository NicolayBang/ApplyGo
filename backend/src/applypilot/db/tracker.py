"""Tracker repository - canonical application record CRUD.

This is the primary interface for creating and querying applications.
The state machine and event log call this to persist transitions.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import asc, desc, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from applypilot.db.models import (
    AnswerLibrary,
    Application,
    ApplicationAnswer,
    ApplicationDocument,
    ApplicationPacketReview,
    Company,
    Document,
    DocumentVersion,
    EventLogEntry,
    ExecutorAction,
    Job,
)
from applypilot.db.models import PolicyDecision as PolicyDecisionRecord
from applypilot.domain.applications.models import (
    ApplicationCreate,
    ApplicationPacketReviewCreate,
    JobCreate,
)
from applypilot.domain.applications.intake import JobIntakeClassifier
from applypilot.domain.applications.scoring import ApplicationScorer, JobScoringInput
from applypilot.domain.companies.normalization import (
    CompanyIdentityCandidate,
    CompanyIdentityNormalizer,
)
from applypilot.domain.executor import ExecutorRequest, ExecutorResult
from applypilot.domain.policy import PolicyDecision, PolicyRequest
from applypilot.domain.state_machine import (
    ApplicationState,
    ApplicationStateMachine,
    InvalidStateTransitionError,
)


# ---------------------------------------------------------------------------
# M5 contract errors (mapped by the router to 400 / 404 / 409)
# ---------------------------------------------------------------------------

class M5Error(Exception):
    """Base class for M5 document/answer/packet contract errors."""


class M5ValidationError(M5Error):
    """Invalid canonical value, blank required field, missing payload, mode, or reference (400)."""


class M5NotFoundError(M5Error):
    """A resource addressed by the request path does not exist (404)."""


class M5ConflictError(M5Error):
    """A uniqueness/idempotency invariant would be violated (409)."""


_CANONICAL_DOC_TYPES = frozenset({"resume", "cover_letter", "supporting", "other"})
_CANONICAL_ROLES = frozenset({"resume", "cover_letter", "supporting", "other"})
_DOCUMENT_NAME_MAX_LENGTH = 256
_QUESTION_KEY_MAX_LENGTH = 256
_EVENT_ACTOR_MAX_LENGTH = 64


def _normalize_actor(actor: object) -> str:
    """Default an absent or blank actor to ``"system"`` after trimming."""
    if isinstance(actor, str):
        trimmed = actor.strip()
        if trimmed:
            return trimmed
    return "system"


def _validate_max_length(value: str, *, field_name: str, maximum: int) -> None:
    """Reject values that exceed their persisted column length before flushing."""
    if len(value) > maximum:
        raise M5ValidationError(f"{field_name} must be at most {maximum} characters")


def _content_checksum(content: str | None, content_json: object) -> str:
    """SHA-256 of a UTF-8, sorted-key canonical JSON envelope of the version payload.

    Matches the deterministic checksum produced by the ``0012`` backfill so a
    re-rendered identical payload yields the same checksum.
    """
    envelope = {"content": content, "content_json": content_json}
    canonical = json.dumps(
        envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


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
        company = self._resolve_company(enriched.company)
        job_data = enriched.model_dump()
        company_source_text = job_data.pop("company")
        job = Job(
            **job_data,
            company_source_text=company_source_text,
            company_id=company.id,
        )
        self._session.add(job)
        self._session.flush()
        return job

    def get_job(self, job_id: uuid.UUID) -> Job | None:
        return self._session.get(Job, job_id)

    def _resolve_company(self, company_text: str | None) -> Company:
        candidate = CompanyIdentityNormalizer().normalize(company_text)

        existing = self._find_company(candidate)
        if existing is not None:
            return existing

        company = Company(
            id=uuid.uuid4(),
            name=candidate.name,
            normalized_name=candidate.normalized_name,
            domain=candidate.domain,
            normalized_domain=candidate.normalized_domain,
        )
        self._session.add(company)
        self._session.flush()
        return company

    def _find_company(self, candidate: CompanyIdentityCandidate) -> Company | None:
        query = self._session.query(Company)
        if candidate.normalized_domain:
            return (
                query.filter(Company.normalized_domain == candidate.normalized_domain)
                .one_or_none()
            )

        return (
            query.filter(Company.normalized_domain.is_(None))
            .filter(Company.normalized_name == candidate.normalized_name)
            .one_or_none()
        )

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
            query = (
                query.join(Application.job)
                .join(Job.company_identity)
                .filter(Company.name.ilike(f"%{company}%"))
            )
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

    # ------------------------------------------------------------------
    # M5 logical document library
    # ------------------------------------------------------------------

    def create_document(self, *, doc_type: str, name: str) -> Document:
        """Create a reusable logical document (no application owner, no content)."""
        if doc_type not in _CANONICAL_DOC_TYPES:
            raise M5ValidationError(f"Unsupported doc_type: {doc_type!r}")
        trimmed_name = name.strip() if isinstance(name, str) else name
        if not trimmed_name:
            raise M5ValidationError("name must not be blank")
        _validate_max_length(
            trimmed_name, field_name="name", maximum=_DOCUMENT_NAME_MAX_LENGTH
        )

        document = Document(doc_type=doc_type, name=trimmed_name)
        self._session.add(document)
        self._session.flush()
        return document

    def list_documents(self) -> list[Document]:
        """Return non-archived logical documents in a deterministic order."""
        return (
            self._session.query(Document)
            .filter(Document.is_archived.is_(False))
            .order_by(
                Document.doc_type.asc(),
                Document.name.asc(),
                Document.created_at.asc(),
                Document.id.asc(),
            )
            .all()
        )

    def get_document(self, document_id: uuid.UUID) -> Document:
        """Return one logical document (including archived); raise if missing."""
        document = self._session.get(Document, document_id)
        if document is None:
            raise M5NotFoundError(f"Document {document_id} not found")
        return document

    def archive_document(self, document_id: uuid.UUID) -> Document:
        """Idempotently hide a document from default reads without deleting it."""
        document = self.get_document(document_id)
        if not document.is_archived:
            document.is_archived = True
            document.updated_at = datetime.now(tz=timezone.utc)
            self._session.flush()
        return document

    def add_document_version(
        self,
        document_id: uuid.UUID,
        *,
        content: str | None = None,
        content_json: dict | None = None,
    ) -> DocumentVersion:
        """Append an immutable version under a row lock; payload is stored verbatim."""
        if content is None and content_json is None:
            raise M5ValidationError("A document version requires content or content_json")

        # Lock the parent document row so the per-document version number is allocated
        # serially; the unique constraint remains the final concurrency guard.
        document = (
            self._session.query(Document)
            .filter(Document.id == document_id)
            .with_for_update()
            .one_or_none()
        )
        if document is None:
            raise M5NotFoundError(f"Document {document_id} not found")

        highest = (
            self._session.query(func.max(DocumentVersion.version_number))
            .filter(DocumentVersion.document_id == document.id)
            .scalar()
        )
        next_version = (highest or 0) + 1

        version = DocumentVersion(
            document_id=document.id,
            version_number=next_version,
            content=content,
            content_json=content_json,
            checksum=_content_checksum(content, content_json),
        )
        self._session.add(version)
        try:
            self._session.flush()
        except IntegrityError as exc:
            raise M5ConflictError(
                f"Version number conflict for document {document_id}"
            ) from exc
        return version

    def list_document_versions(self, document_id: uuid.UUID) -> list[DocumentVersion]:
        """Return a document's immutable versions in ascending version order."""
        self.get_document(document_id)
        return (
            self._session.query(DocumentVersion)
            .filter(DocumentVersion.document_id == document_id)
            .order_by(DocumentVersion.version_number.asc())
            .all()
        )

    def get_document_version(self, version_id: uuid.UUID) -> DocumentVersion:
        """Return one immutable version; raise if missing."""
        version = self._session.get(DocumentVersion, version_id)
        if version is None:
            raise M5NotFoundError(f"Document version {version_id} not found")
        return version

    # ------------------------------------------------------------------
    # M5 answer library
    # ------------------------------------------------------------------

    def create_answer(
        self,
        *,
        question_key: str,
        question_text: str,
        answer_text: str,
    ) -> AnswerLibrary:
        """Create a reusable library answer; question/answer text is stored verbatim."""
        key = question_key.strip() if isinstance(question_key, str) else question_key
        if not key:
            raise M5ValidationError("question_key must not be blank")
        _validate_max_length(
            key, field_name="question_key", maximum=_QUESTION_KEY_MAX_LENGTH
        )

        existing = (
            self._session.query(AnswerLibrary)
            .filter(AnswerLibrary.question_key == key, AnswerLibrary.is_archived.is_(False))
            .one_or_none()
        )
        if existing is not None:
            raise M5ConflictError(f"An active answer already exists for question_key {key!r}")

        answer = AnswerLibrary(
            question_key=key,
            question_text=question_text,
            answer_text=answer_text,
        )
        self._session.add(answer)
        try:
            self._session.flush()
        except IntegrityError as exc:
            raise M5ConflictError(
                f"An active answer already exists for question_key {key!r}"
            ) from exc
        return answer

    def list_answers(self) -> list[AnswerLibrary]:
        """Return non-archived library answers ordered by question_key, then id."""
        return (
            self._session.query(AnswerLibrary)
            .filter(AnswerLibrary.is_archived.is_(False))
            .order_by(AnswerLibrary.question_key.asc(), AnswerLibrary.id.asc())
            .all()
        )

    def get_answer(self, answer_id: uuid.UUID) -> AnswerLibrary:
        """Return one library answer (including archived); raise if missing."""
        answer = self._session.get(AnswerLibrary, answer_id)
        if answer is None:
            raise M5NotFoundError(f"Answer {answer_id} not found")
        return answer

    def update_answer(
        self,
        answer_id: uuid.UUID,
        *,
        question_text: str | None = None,
        answer_text: str | None = None,
    ) -> AnswerLibrary:
        """Edit the current library answer in place; never touches ``question_key``."""
        answer = self.get_answer(answer_id)
        if question_text is None and answer_text is None:
            raise M5ValidationError(
                "At least one of question_text or answer_text is required"
            )
        if question_text is not None:
            answer.question_text = question_text
        if answer_text is not None:
            answer.answer_text = answer_text
        answer.updated_at = datetime.now(tz=timezone.utc)
        self._session.flush()
        return answer

    def archive_answer(self, answer_id: uuid.UUID) -> AnswerLibrary:
        """Idempotently archive a library answer, freeing its active key."""
        answer = self.get_answer(answer_id)
        if not answer.is_archived:
            answer.is_archived = True
            answer.updated_at = datetime.now(tz=timezone.utc)
            self._session.flush()
        return answer

    # ------------------------------------------------------------------
    # M5 application attachments and answer snapshots (append-only)
    # ------------------------------------------------------------------

    def attach_document(
        self,
        application_id: uuid.UUID,
        *,
        document_version_id: uuid.UUID,
        role: str,
        display_order: int,
        actor: str | None = None,
    ) -> ApplicationDocument:
        """Append an attachment binding one exact document version to an application."""
        if self._session.get(Application, application_id) is None:
            raise M5NotFoundError(f"Application {application_id} not found")
        if role not in _CANONICAL_ROLES:
            raise M5ValidationError(f"Unsupported document role: {role!r}")
        if display_order < 0:
            raise M5ValidationError("display_order must be non-negative")

        version = self._session.get(DocumentVersion, document_version_id)
        if version is None:
            raise M5ValidationError(f"Document version {document_version_id} not found")

        existing = (
            self._session.query(ApplicationDocument)
            .filter(
                ApplicationDocument.application_id == application_id,
                ApplicationDocument.document_version_id == document_version_id,
                ApplicationDocument.role == role,
            )
            .one_or_none()
        )
        if existing is not None:
            raise M5ConflictError(
                "This document version is already attached to the application with this role"
            )

        actor_name = _normalize_actor(actor)
        _validate_max_length(
            actor_name, field_name="actor", maximum=_EVENT_ACTOR_MAX_LENGTH
        )
        attachment = ApplicationDocument(
            application_id=application_id,
            document_version_id=document_version_id,
            role=role,
            display_order=display_order,
        )
        self._session.add(attachment)
        try:
            self._session.flush()
        except IntegrityError as exc:
            raise M5ConflictError(
                "This document version is already attached to the application with this role"
            ) from exc
        self._session.refresh(attachment)

        self._append_event(
            application_id=application_id,
            event_type="application_document.attached",
            actor=actor_name,
            payload={
                "application_id": str(application_id),
                "application_document_id": str(attachment.id),
                "document_version_id": str(document_version_id),
                "role": role,
                "version_number": version.version_number,
                "actor": actor_name,
                "created_at": attachment.created_at.isoformat(),
            },
        )
        return attachment

    def list_application_documents(
        self, application_id: uuid.UUID
    ) -> list[ApplicationDocument]:
        """Return an application's attachments in deterministic projection order."""
        if self._session.get(Application, application_id) is None:
            raise M5NotFoundError(f"Application {application_id} not found")
        return (
            self._session.query(ApplicationDocument)
            .filter(ApplicationDocument.application_id == application_id)
            .order_by(
                ApplicationDocument.display_order.asc(),
                ApplicationDocument.created_at.asc(),
                ApplicationDocument.id.asc(),
            )
            .all()
        )

    def record_application_answer(
        self,
        application_id: uuid.UUID,
        *,
        answer_library_id: uuid.UUID | None = None,
        question_key: str | None = None,
        question_text: str | None = None,
        answer_text: str | None = None,
        actor: str | None = None,
    ) -> ApplicationAnswer:
        """Record an immutable answer snapshot in sourced or manual mode."""
        if self._session.get(Application, application_id) is None:
            raise M5NotFoundError(f"Application {application_id} not found")

        if answer_library_id is not None:
            if any(v is not None for v in (question_key, question_text, answer_text)):
                raise M5ValidationError(
                    "Sourced answer snapshot must not include manual question/answer fields"
                )
            library = self._session.get(AnswerLibrary, answer_library_id)
            if library is None:
                raise M5ValidationError(
                    f"Answer library entry {answer_library_id} not found"
                )
            snapshot_key = library.question_key
            snapshot_question = library.question_text
            snapshot_answer = library.answer_text
            provenance: uuid.UUID | None = answer_library_id
        else:
            if question_key is None or question_text is None or answer_text is None:
                raise M5ValidationError(
                    "Manual answer snapshot requires question_key, question_text, and answer_text"
                )
            snapshot_key = question_key.strip() if isinstance(question_key, str) else question_key
            if not snapshot_key:
                raise M5ValidationError("question_key must not be blank")
            snapshot_question = question_text
            snapshot_answer = answer_text
            provenance = None

        existing = (
            self._session.query(ApplicationAnswer)
            .filter(
                ApplicationAnswer.application_id == application_id,
                ApplicationAnswer.question_key == snapshot_key,
            )
            .one_or_none()
        )
        if existing is not None:
            raise M5ConflictError(
                f"Application already has an answer for question_key {snapshot_key!r}"
            )

        actor_name = _normalize_actor(actor)
        _validate_max_length(
            actor_name, field_name="actor", maximum=_EVENT_ACTOR_MAX_LENGTH
        )
        snapshot = ApplicationAnswer(
            application_id=application_id,
            answer_library_id=provenance,
            question_key=snapshot_key,
            question_text=snapshot_question,
            answer_text=snapshot_answer,
        )
        self._session.add(snapshot)
        try:
            self._session.flush()
        except IntegrityError as exc:
            raise M5ConflictError(
                f"Application already has an answer for question_key {snapshot_key!r}"
            ) from exc
        self._session.refresh(snapshot)

        self._append_event(
            application_id=application_id,
            event_type="application_answer.recorded",
            actor=actor_name,
            payload={
                "application_id": str(application_id),
                "application_answer_id": str(snapshot.id),
                "answer_library_id": str(provenance) if provenance is not None else None,
                "question_key": snapshot_key,
                "actor": actor_name,
                "created_at": snapshot.created_at.isoformat(),
            },
        )
        return snapshot

    def list_application_answers(
        self, application_id: uuid.UUID
    ) -> list[ApplicationAnswer]:
        """Return an application's immutable answer snapshots ordered by created_at, id."""
        if self._session.get(Application, application_id) is None:
            raise M5NotFoundError(f"Application {application_id} not found")
        return (
            self._session.query(ApplicationAnswer)
            .filter(ApplicationAnswer.application_id == application_id)
            .order_by(ApplicationAnswer.created_at.asc(), ApplicationAnswer.id.asc())
            .all()
        )

    def get_packet(self, application_id: uuid.UUID) -> dict[str, object]:
        """Project the application packet read model from immutable M5 records + M2 review."""
        application = self._session.get(Application, application_id)
        if application is None:
            raise M5NotFoundError(f"Application {application_id} not found")

        reviews = self.get_packet_reviews(application_id)
        return {
            "application": application,
            "documents": self.list_application_documents(application_id),
            "answers": self.list_application_answers(application_id),
            "latest_packet_review": reviews[-1] if reviews else None,
        }
