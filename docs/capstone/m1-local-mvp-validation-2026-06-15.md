# M1 Local MVP Validation - 2026-06-15

**Status:** Passed for M1 MVP closeout
**Environment:** Local Windows machine, Docker Desktop, Docker Compose `app` profile
**Branch tested:** `main`
**Backend:** FastAPI + PostgreSQL with migrations applied by Compose

This note records the final local validation used to close the M1 MVP demo path. It confirms that
the packaged Docker environment can serve the backend and dashboard together, and that the frontend
can create records that are visible through the backend API and audit endpoints.

## Environment Checks

| Check | Result |
| --- | --- |
| Docker Desktop engine running | Pass |
| `docker compose --profile app up -d api` | Pass |
| PostgreSQL container healthy | Pass |
| Redis container running | Pass |
| Migration service completed | Pass |
| `GET /health` | Pass |
| `GET /ui/` | Pass |

## Frontend To Backend Check

The dashboard was opened at:

```text
http://localhost:8000/ui/
```

Manual action performed:

1. Created a job/application from the dashboard.
2. Checked the backend `GET /applications` endpoint.
3. Checked the created application's audit endpoint.

Observed backend record:

```text
Application ID: f842bc7f-5544-4404-9380-f9b3ce74a187
Job ID: 894321ad-f5c5-4e5d-82f8-07617f44df5d
Location: Remote
State: ApplicationCreated
```

The role and company fields were persisted from the manual dashboard input. The exact sample text
was not important for this check; the validation target was frontend-to-backend creation,
persistence, retrieval, and audit logging.

Observed audit evidence:

```text
event_type: application.created
to_state: ApplicationCreated
actor: system
payload.automation_mode: manual
```

## Result

M1 is MVP-presentable for capstone review. The implemented system demonstrates:

- local Docker startup;
- backend health check;
- dashboard serving from the packaged backend;
- frontend job/application creation;
- PostgreSQL-backed persistence;
- backend API retrieval;
- append-only creation audit event.

This validation does not add or approve new product scope. Real external submission, Gmail
automation, browser automation, LLM drafting, multi-user authentication, production deployment, and
future normalized company/contact/document/thread tables remain out of M1 scope.
