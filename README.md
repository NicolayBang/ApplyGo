# ApplyPilot

ApplyPilot is a governed job application automation platform built from the locked OpenClaw architecture baseline.

## Locked architecture principles

- Workflow owns state.
- Database owns truth.
- Policy engine owns permission.
- LLMs are limited to extraction, classification, scoring support, and drafting.
- Workers execute approved actions only through a shared executor contract.
- Dry-run is a first-class platform capability from day one.
- Semi-auto and full-auto are policy modes on the same workflow.

## Milestone 1 scope

This repository currently contains the Milestone 1 platform spine.

Milestone 1 focuses on the platform spine:

- Canonical data model and tracker
- Application state machine
- Append-only event log
- Policy engine and automation modes
- Executor contract with `execute` and `dry_run`
- Stub executor that logs planned actions, safeguards, and side-effect status
- Minimal dashboard for tracker, workflow state, scoring, policy, dry-run, review readiness, and audit visibility

No Gmail, browser automation, LLM integration, or real external submission behavior is implemented yet.

## M1 demo path

The current dashboard demo flow is:

```text
manual intake -> parse/classify -> state progression -> scoring -> policy check -> dry-run executor -> review readiness -> audit timeline
```

Useful reviewer entry points:

- `docs/capstone/README.md`: capstone documentation index and suggested reading order
- `docs/capstone/mvp-status.md`: concise current implementation status and remaining MVP boundaries
- `docs/capstone/dashboard-demo-flow.md`: step-by-step dashboard demo runbook
- `docs/capstone/m1-demo-review-checklist.md`: manual pass/fix checklist for reviewing the M1 demo
- `docs/architecture/current-data-model.md`: implemented M1 data model snapshot
- `docs/architecture/database-implementation-roadmap.md`: done/next/future PostgreSQL plan and contract readiness
- `docs/contracts/database-schema-contract.md`: exact M1 PostgreSQL table and constraint contract
- `docs/diagrams/README.md`: diagram index and diagram authority reminder
- `docs/diagrams/database-schema.md`: separate implemented and planned ER views
- `docs/devops/codespaces.md`: Codespaces and DB-backed validation workflow
- `docs/team/README.md`: virtual team persona index and advisory boundaries
- `docs/architecture/locked-plan.md`: architecture authority and M1 scope

The dashboard includes a `Sample job` prefill button so reviewers can run the demo path without manually typing the sample role.

## Repository layout

- `backend/`: FastAPI backend, domain boundaries, and worker placeholders
- `frontend/`: static M1 audit dashboard served by the backend at `/ui`
- `docs/architecture/`: implementation notes tied to the locked plan

## Initial stack

- Backend: FastAPI
- Database: PostgreSQL
- Queue/cache: Redis
- Browser automation: Playwright later
- Email: Gmail API later
- Documents: docxtpl / python-docx later
- Deployment: Docker Compose first

## Getting started

1. Copy `.env.example` to `.env` and adjust values.
2. Start local services with Docker Compose.
3. Run database migrations.
4. Create a Python virtual environment inside `backend/`.
5. Install backend dependencies.
6. Run the FastAPI app.

Example commands:

```powershell
Copy-Item .env.example .env
docker compose up -d postgres redis
docker compose run --rm migrate
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
uvicorn applypilot.main:app --reload
```

## Validation

For DB-backed validation in Codespaces or local Docker, use `docs/devops/codespaces.md`.

The full M1 validation path runs migrations, backend tests, and the seed-to-dashboard check:

```powershell
docker compose up -d postgres redis
docker compose run --rm migrate
cd backend
python -m pytest
python -m scripts.validate_seed_to_dashboard
```

The Compose migration runner uses the same Alembic migration chain as local backend commands. For
an optional demo seed and audit validation inside Compose, run:

```powershell
docker compose --profile demo run --rm seed
```

## Definition of done for milestone 1

- Create an application record
- Parse and classify basic job metadata
- Transition through states
- Log every event
- Evaluate policy
- Simulate an executor action in dry-run with plan details and no side effects
- Inspect it in the dashboard
- Inspect review readiness and audit evidence in the dashboard

## Non-goals in v1

- Multi-account orchestration
- Captcha bypassing or anti-bot evasion
- Autonomous custom, salary, legal, or disclosure answers
- Unsupported ATS flows
- Full event sourcing
- LLM access to credentials
