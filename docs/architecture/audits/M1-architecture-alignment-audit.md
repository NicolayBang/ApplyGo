# M1 Architecture Alignment Audit

Status: Review snapshot  
Date: 2026-06-14  
Scope: Current code, tests, CI, and repository documentation compared with founding architecture rules.

## Sources Checked

- `docs/architecture/OpenClaw_Final_Agreed_Architecture.pdf`
- `AGENTS.md`
- `docs/architecture/locked-plan.md`
- `docs/decisions/ADR-0001-architecture-operating-structure.md`
- `docs/decisions/ADR-0002-canonical-data-model.md`
- `docs/contracts/event-log-contract.md`
- `docs/contracts/policy-contract.md`
- `docs/contracts/executor-contract.md`
- `docs/contracts/database-schema-contract.md`
- Backend API, tracker, domain, ORM, migration, test, and CI files.
- Frontend dashboard files and frontend CI syntax gate.

## Overall Verdict

The current implementation is strongly aligned with the founding M1 architecture.

Estimated alignment: about 85%.

The core control-plane promise is intact:

- governed workflow platform, not a loose autonomous AI bot;
- workflow owns state;
- PostgreSQL owns durable truth;
- policy owns permission;
- dry-run is first-class;
- important decisions and executor activity are auditable;
- M1 remains a platform spine, not real Gmail, browser, or autonomous submission automation.

## Strong Alignment

### Workflow and State

- Application state is represented by the M1 state machine.
- State transitions go through `Tracker.update_state()`.
- State changes append `application.state_changed` audit events.
- The API now protects `Submitted` behind policy and executor evidence.

### Policy Before Executor

- Policy evaluation is explicit and persisted before executor dry-run.
- Dry-run executor requests require a recorded, allowed policy decision for the same application.
- Policy decisions append `policy_decision_logged` events.

### Dry-Run First

- The exposed executor path is dry-run only.
- `StubExecutor` returns planned results with `side_effects=false` for dry-run.
- No live Gmail, browser, document submission, or external automation is implemented in M1.

### Auditability

- Application creation, scoring, state transitions, policy decisions, executor attempts, and executor results are recorded.
- Event vocabulary is aligned around the implemented `application.*`, `policy_decision_logged`, `executor_attempt_logged`, and `executor_result_logged` names.
- `event_log` no longer cascades on application delete at the database level.
- ORM event relationships avoid delete/delete-orphan cascade and use passive deletes.

### Database and Documentation

- Current M1 database truth is documented separately from proposed future normalization.
- ADR-0002 is correctly marked Proposed and does not authorize migrations yet.
- Open database decisions are explicitly documented instead of hidden.

### Test and CI Coverage

- Backend ruff passes.
- Full backend pytest passes.
- Frontend JavaScript syntax gate passes.
- CI includes backend migration/test gates and a frontend syntax gate.

## Gaps and Risks

### Executor Contract Shape Alignment

The executor contract document describes request and response metadata now represented in the
dataclass implementation:

- `request_id`
- `worker`
- `requested_by`
- `requested_at`

Assessment: resolved after the executor request metadata alignment PR. `ExecutorRequest`,
`ExecutorResult`, API schemas, persisted executor actions, audit events, and tests now carry
the contract metadata.

Recommended follow-up: keep real worker implementations behind this contract and avoid adding
side effects until policy and executor evidence remain visible in the dashboard.

### Submission Guard Location

The `Submitted` prerequisite check now lives at the tracker workflow boundary.

Assessment: resolved after the submitted-transition hardening PR. `Tracker.update_state()` rejects
direct transitions to `Submitted`, and `Tracker.submit_application()` verifies the required
evidence before moving an application from `Approved` to `Submitted`.

The enforced path is:

```text
Approved + allowed policy decision + matching executor result -> Submitted
```

Evidence:

- `backend/src/applypilot/db/tracker.py`
- `backend/tests/unit/test_tracker_submission_workflow.py`
- `backend/tests/integration/test_application_api.py`

### Policy and Executor Retention

Event logs, policy decisions, and executor actions survive application deletion at the database
foreign-key layer.

Assessment: resolved for M1 by ADR-0004 and migration `0007`. Physical deletion is restricted while
audit-bearing records reference an application.

Recommended follow-up: keep long-term retention, privacy redaction, and archive behavior explicit
before delete/archive behavior becomes user-facing or compliance-sensitive.

### PostgreSQL-Backed Validation

The local full test suite skips the seed-to-dashboard test when PostgreSQL is unavailable.

Assessment: acceptable locally, because CI and Copilot validation can run PostgreSQL-backed checks. Continue using Codespaces or CI validation for migration-sensitive PRs.

Recommended follow-up: keep posting exact Copilot validation prompts when local PostgreSQL is not running and migrations or DB behavior change.

## Current Validation Snapshot

Commands run during this audit:

```bash
python -m ruff check .
python -m pytest
node --check frontend/app.js
```

Results:

- Backend ruff: passed.
- Backend pytest: 58 passed, 1 skipped.
- Frontend syntax check: passed.

The skipped test is the existing PostgreSQL-backed seed-to-dashboard test when local PostgreSQL is not available.

## Candidate Future Implementation PR

Once Francis review is complete and the team explicitly confirms implementation timing, the next
logical implementation PR would be:

```text
feat(db): implement approved M3 company identity migration
```

Goal:

- Add the `companies` table and `jobs.company_id` only after Francis review, explicit timing
  approval, and approval of the proposed M3 company identity and migration contracts.
- Preserve `jobs.company` as source/provenance text during the compatibility period.
- Include PostgreSQL-backed migration, backfill, API/dashboard compatibility, and seed-to-dashboard
  validation.

Do not start this implementation while Francis review is pending or before the proposed M3
contracts are explicitly approved for implementation.

This would move ApplyPilot beyond the M1 platform spine only after the required human approval gate.
