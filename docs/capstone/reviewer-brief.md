# ApplyPilot Reviewer Brief

**Status:** Milestone 1 capstone MVP candidate  
**Audience:** recruiters, instructors, and technical reviewers

ApplyPilot is a governed job application automation platform. The current milestone proves the
platform spine: manual job intake, deterministic classification and scoring, workflow state
transitions, policy evaluation, side-effect-free dry-run execution, and audit visibility.

This is not a finished job application product. Gmail automation, browser automation, LLM drafting,
multi-user auth, production hosting, and real external submission are intentionally out of scope for
M1.

## What Was Built

- FastAPI backend with domain modules for applications, state machine, policy, executor contracts,
  and deterministic scoring/classification.
- PostgreSQL-backed persistence with Alembic migrations for jobs, applications, events, policy
  decisions, and executor actions.
- Append-only audit trail for creation, state changes, scoring, policy decisions, and executor
  attempt/result records.
- Governed dry-run executor that records planned actions and explicitly reports no external side
  effects.
- Static dashboard served by FastAPI at `/ui/`, with manual intake, recent applications, guided
  next actions, lifecycle stepper, score details, policy decisions, executor preview, review
  readiness, and audit timeline.
- Docker Compose and Codespaces workflows for reproducible PostgreSQL/Redis-backed validation.
- GitHub CI for frontend syntax, backend linting, migrations, tests, and app import smoke checks.

## Architecture Highlights

- Workflow owns state.
- Database owns truth.
- Policy engine owns permission.
- Executor calls require a recorded policy decision.
- Dry-run is a first-class path and does not perform real external actions.
- `Submitted` is guarded behind approved workflow state plus policy/executor evidence.
- Planned future architecture is kept separate from implemented M1 behavior.

## Validation Evidence

Current validation covers:

- backend linting with Ruff;
- unit and integration tests for state transitions, policy outcomes, executor idempotency,
  audit retention, API behavior, dashboard asset contracts, and documentation links;
- Alembic migration execution against PostgreSQL in CI;
- DB-backed seed-to-dashboard validation through Docker/Codespaces;
- manual demo runbook and pass/fix checklist under `docs/capstone/`.

Recommended reviewer path:

1. Read `docs/capstone/mvp-status.md`.
2. Run `docs/capstone/dashboard-demo-flow.md`.
3. Record pass/fix notes with `docs/capstone/m1-demo-review-checklist.md`.

## AI-Assisted Development Disclosure

AI tools were used as pair-programming, review, and validation assistants. Humans owned the product
scope, architecture decisions, merge decisions, and final acceptance. AI-generated suggestions were
kept behind repository rules, tests, CI, contracts, and human review.

The project is intentionally presented as an engineered capstone, not as autonomous AI output.
