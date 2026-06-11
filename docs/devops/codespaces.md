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

## Usage Reminder
Stop Codespaces when done to avoid unnecessary usage and cost:
- Stop containers with `docker compose down`.
- Stop the Codespace from the GitHub Codespaces UI.
