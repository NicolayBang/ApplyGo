# Codespaces Development Guide

## Purpose of Codespaces
GitHub Codespaces provides a cloud development environment for ApplyPilot when local machine setup is restricted or inconsistent.

This repository keeps local Docker and Codespaces aligned by using one shared runtime definition: `docker-compose.yml`.

## When to Use Codespaces vs Local Docker
Use Codespaces when:
- Local admin policy blocks Docker or WSL setup.
- You need a consistent environment across contributors.
- You want quick onboarding without machine-specific installs.

Use local Docker when:
- You already have Docker working reliably.
- You prefer local performance and offline iteration.

In both cases, `docker-compose.yml` remains the source of truth.

## Open the Repo in Codespaces
1. Open the repository on GitHub.
2. Click Code.
3. Select Codespaces.
4. Create codespace on branch `feature/APP-002-codespaces-support` (or target branch).
5. Wait for devcontainer setup to finish.

## Start and Stop the Environment
Start services:
```bash
cd /workspaces/ApplyPilot
docker compose up -d
```

Stop services:
```bash
cd /workspaces/ApplyPilot
docker compose down
```

## Run Docker Compose
Compose usage is unchanged between local and Codespaces:
```bash
cd /workspaces/ApplyPilot
docker compose up -d
docker compose ps
```

## Verification Checklist
From repository root in Codespaces:

1. Backend starts
```bash
cd backend
python -m uvicorn applypilot.main:app --host 0.0.0.0 --port 8000
```

2. PostgreSQL reachable
```bash
cd /workspaces/ApplyPilot
docker compose exec postgres pg_isready -U ${POSTGRES_USER:-applypilot} -d ${POSTGRES_DB:-applypilot}
```

3. Redis reachable
```bash
cd /workspaces/ApplyPilot
docker compose exec redis redis-cli ping
```
Expected output: `PONG`

4. Health endpoint returns ok
```bash
curl -s http://127.0.0.1:8000/health
```
Expected response contains `"status": "ok"`.

## DB-Backed Validation Workflow

Use this workflow when a change touches migrations, database-backed tracker behavior, demo seed data, the audit endpoint, or dashboard validation.

Start shared services from the repository root:

```bash
docker compose up -d postgres redis
```

Run backend validation from `backend/`:

```bash
cd backend
python -m pip install -e ".[dev]"
python -m ruff check .
python -m alembic upgrade head
python -m pytest
python -m compileall src tests alembic scripts
python -m scripts.validate_seed_to_dashboard
```

For the focused seed-to-dashboard check:

```bash
cd backend
python -m alembic upgrade head
python -m pytest tests/integration/test_seed_to_dashboard.py -v
python -m scripts.validate_seed_to_dashboard
```

The DB-backed seed-to-dashboard test skips when PostgreSQL is unavailable. In Codespaces and CI, PostgreSQL should be running and the test should execute against a migrated schema.

CI runs `python -m alembic upgrade head` before `python -m pytest` so database-backed tests validate the real migration path instead of creating tables directly.

## Usage Reminder
Stop Codespaces when done to avoid unnecessary usage and cost:
- Stop containers with `docker compose down`.
- Stop the Codespace from the GitHub Codespaces UI.

## APP-001 Closure Record
Date: 2026-06-11

Validation evidence:
- [x] `docker compose up -d` succeeded in Codespaces.
- [x] `docker compose ps` showed `applypilot-postgres` and `applypilot-redis` in Up state.
- [x] `alembic upgrade head` succeeded from `backend`.
- [x] Repository status clean and synchronized on `main`.

Governance decision:
- Outcome: done
- Blocker: none
- Human signoff: approved in chat with explicit "go" instruction.
