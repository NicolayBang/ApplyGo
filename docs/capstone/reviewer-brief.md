# ApplyPilot Reviewer Brief

**Status:** Milestone 1 MVP-presentable capstone baseline
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

![Current dashboard review evidence](assets/m2-dashboard-review-evidence.png)

## Architecture Highlights

- Workflow owns state.
- Database owns truth.
- Policy engine owns permission.
- Executor calls require a recorded policy decision.
- Dry-run is a first-class path and does not perform real external actions.
- `Submitted` is guarded behind approved workflow state plus policy/executor evidence.
- Planned future architecture is kept separate from implemented M1 behavior.

## Key Tradeoffs

- **Dry-run before execution:** M1 proves the executor contract and audit trail without sending
  email, opening browsers, or submitting applications externally.
- **Policy before executor:** Executor actions require recorded policy decisions so reviewers can
  see why an action was allowed, blocked, or sent to human review.
- **Deterministic first pass:** Classification and scoring are rule-based for M1 so the demo is
  repeatable and testable before adding LLM-assisted extraction or drafting.
- **Small monolith over microservices:** The current FastAPI app keeps domain boundaries explicit
  while avoiding premature distributed-system complexity.
- **Documentation with boundaries:** Future ideas are documented, but implemented M1 behavior is
  called out separately to avoid overstating the product.

## Validation Evidence

Current validation covers:

- backend linting with Ruff;
- unit and integration tests for state transitions, policy outcomes, executor idempotency,
  audit retention, API behavior, dashboard asset contracts, and documentation links;
- Alembic migration execution against PostgreSQL in CI;
- DB-backed seed-to-dashboard validation through Docker/Codespaces;
- manual demo runbook and pass/fix checklist under `docs/capstone/`.
- final local frontend-backend validation recorded in `docs/capstone/m1-local-mvp-validation-2026-06-15.md`.

Recommended reviewer path:

1. Read `docs/capstone/mvp-status.md`.
2. Read `docs/capstone/m1-release-notes.md`.
3. Use `docs/capstone/m1-demo-script.md` for a live walkthrough.
4. Run `docs/capstone/dashboard-demo-flow.md` for detailed validation.
5. Record pass/fix notes with `docs/capstone/m1-demo-review-checklist.md`.

## AI-Assisted Development Disclosure

AI tools were used as pair-programming, review, and validation assistants. Humans owned the product
scope, architecture decisions, merge decisions, and final acceptance. AI-generated suggestions were
kept behind repository rules, tests, CI, contracts, and human review.

The project is intentionally presented as an engineered capstone, not as autonomous AI output.
