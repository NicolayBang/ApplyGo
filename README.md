# ApplyPilot

ApplyPilot is a governed job application automation platform scaffolded from the locked OpenClaw architecture baseline.

## Locked architecture principles

- Workflow owns state.
- Database owns truth.
- Policy engine owns permission.
- LLMs are limited to extraction, classification, scoring support, and drafting.
- Workers execute approved actions only through a shared executor contract.
- Dry-run is a first-class platform capability from day one.
- Semi-auto and full-auto are policy modes on the same workflow.

## Milestone 1 scope

This repository currently contains scaffolding only.

Milestone 1 focuses on the platform spine:

- Canonical data model and tracker
- Application state machine
- Append-only event log
- Policy engine and automation modes
- Executor contract with `execute` and `dry_run`
- Stub executor that logs planned actions
- Minimal dashboard placeholder for tracker and audit visibility

No Gmail, browser automation, LLM integration, or business logic is implemented yet.

## Repository layout

- `backend/`: FastAPI backend, domain boundaries, and worker placeholders
- `frontend/`: placeholder for the future dashboard app
- `infra/`: local infrastructure notes and container support files
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
3. Create a Python virtual environment inside `backend/`.
4. Install backend dependencies.
5. Run the FastAPI app.

Example commands:

```powershell
Copy-Item .env.example .env
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
uvicorn applypilot.main:app --reload
```

## Definition of done for milestone 1

- Create an application record
- Transition through states
- Log every event
- Evaluate policy
- Simulate an executor action in dry-run
- Inspect it in the dashboard

## Non-goals in v1

- Multi-account orchestration
- Captcha bypassing or anti-bot evasion
- Autonomous custom, salary, legal, or disclosure answers
- Unsupported ATS flows
- Full event sourcing
- LLM access to credentials
