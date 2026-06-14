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

### Executor Contract Shape Drift

The executor contract document describes a fuller request and response shape than the current dataclass implementation.

Contract fields not yet represented directly in `ExecutorRequest` include:

- `request_id`
- `worker`
- `requested_by`
- `requested_at`

Assessment: acceptable for early M1, but this is the clearest contract drift.

Recommended follow-up: align the executor dataclasses, schemas, stored payloads, and tests with the contract before adding real worker implementations.

### Submission Guard Location

The `Submitted` prerequisite check currently lives at the API layer.

Assessment: useful and correct for dashboard/API usage, but the core workflow would be stronger if submission were a dedicated workflow command or tracker method. That would prevent future internal callers from bypassing the same guard by calling a generic state update directly.

Recommended follow-up: add a `submit_application` workflow service or tracker method that enforces:

```text
Approved + allowed policy decision + matching executor result -> Submitted
```

### Policy and Executor Retention

Event logs survive application deletion, but `policy_decisions` and `executor_actions` still cascade with applications.

Assessment: this is not hidden drift because it is documented as an open database decision. It should be resolved before delete/archive behavior becomes user-facing or compliance-sensitive.

Recommended follow-up: decide whether policy and executor records are operational children or durable audit records.

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

## Recommended Next PR

Next logical implementation PR:

```text
feat(workflow): centralize submitted transition prerequisites
```

Goal:

- Move submission prerequisite enforcement out of the router and into a dedicated workflow boundary.
- Keep the generic state machine intact.
- Add runnable tests proving that only the guarded workflow can move an application from `Approved` to `Submitted`.

This would close the most important remaining architecture gap without expanding M1 scope.
