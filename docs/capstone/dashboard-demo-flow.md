# Dashboard Demo Flow

**Status:** Milestone 1 demo runbook  
**Audience:** reviewers, instructors, recruiters, and contributors  
**Scope:** local Docker or GitHub Codespaces

This guide demonstrates the implemented M1 platform spine:

```text
manual intake -> state progression -> scoring -> policy check -> dry-run executor -> audit timeline
```

The demo uses the current backend, PostgreSQL, and the static dashboard served by FastAPI at `/ui`.

## Prerequisites

- Docker or GitHub Codespaces
- Python dependencies installed for the backend
- Repository root as the starting directory

For Codespaces setup details, see `docs/devops/codespaces.md`.

## Start Services

From the repository root:

```bash
docker compose up -d postgres redis
```

Run database migrations:

```bash
cd backend
python -m alembic upgrade head
```

Start the backend:

```bash
python -m uvicorn applypilot.main:app --host 0.0.0.0 --port 8000
```

Expected health check:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok","service":"applypilot"}
```

## Open The Dashboard

Open:

```text
http://127.0.0.1:8000/ui/
```

In Codespaces, open the forwarded port `8000` URL and add `/ui/`.

The dashboard should show:

- manual intake form
- workflow actions
- application summary
- score details
- policy decisions
- executor actions
- audit timeline

## Demo Script

### 1. Create A Manual Application

In the manual intake form, enter sample data:

```text
Role title: Backend Platform Engineer
Company: ApplyPilot Demo Co.
Location: Remote
Job URL: https://example.com/jobs/backend-platform-engineer
Remote ok: checked
```

Paste a job description:

```text
Build Python APIs with FastAPI, PostgreSQL, automation workflows, and platform data services.
Partner with DevOps and product teams to improve reliable backend delivery.
```

Click `Create`.

Expected result:

- status message says the application was created
- application ID field is populated
- application summary loads with state `ApplicationCreated`
- audit timeline includes `application.created`

### 2. Progress Workflow State

Use the state buttons in the workflow panel.

Recommended demo path:

```text
ApplicationCreated -> Draft -> ReadyForReview -> Approved
```

Expected result:

- state value updates in the application summary
- each transition appends `application.state_changed`
- audit timeline shows `from_state`, `to_state`, and dashboard payload metadata

Invalid transitions are rejected by the backend state machine.

### 3. Score The Application

Click `Score application`.

Expected result:

- fit score appears in the application summary
- confidence appears as `high`, `medium`, or `low`
- recommendation appears as `recommended`, `needs_review`, or `not_recommended`
- score details show reasons, risks, missing data, and red flags
- audit timeline includes `application.scored`

The current scorer is deterministic and does not call an LLM.

### 4. Evaluate Policy

Click `Evaluate policy`.

Expected result:

- policy decision is recorded
- decision appears in the policy decisions panel
- audit timeline includes `policy_decision_logged`

The policy check uses stored application score context when explicit context is not provided by the dashboard.

### 5. Dry-Run Follow-Up

Click `Dry-run follow-up`.

Expected result:

- executor action is created with execution mode `dry_run`
- executor status is `planned`
- audit timeline includes:
  - `executor_attempt_logged`
  - `executor_result_logged`

The dry-run executor records the planned action only. It does not send email, open a browser, or submit anything externally.

## Validation Commands

Run backend checks from `backend/`:

```bash
python -m ruff check .
python -m pytest
```

Run the DB-backed seed-to-dashboard validation:

```bash
python -m pytest tests/integration/test_seed_to_dashboard.py -v
python -m scripts.validate_seed_to_dashboard
```

Expected result:

- migrations apply cleanly
- backend tests pass
- seed-to-dashboard validation passes
- dashboard audit endpoint returns application, policy, executor, and event records

## What This Demo Proves

- The database owns durable truth.
- The workflow state machine controls valid application progression.
- Policy decisions are recorded before executor actions.
- Dry-run execution is first-class and side-effect free.
- The audit timeline records important workflow events.
- Human review remains central; the system supports governed automation rather than loose autonomous action.

## Current Non-Goals

This demo does not include:

- Gmail automation
- browser automation
- real application submission
- LLM extraction or drafting
- production deployment
- multi-user authentication

These remain future milestone work.
