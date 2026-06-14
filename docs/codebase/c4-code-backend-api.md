# C4 Code Level: Backend API Router

## Overview

- **Location**: `backend/src/applypilot/api/router.py`
- **Framework**: FastAPI
- **Purpose**: Expose the implemented Milestone 1 workflow through HTTP.
- **Dependency boundary**: Application endpoints receive a `TrackerUnitOfWork`.

## Endpoints

| Method | Path | Handler | Result |
|---|---|---|---|
| `GET` | `/health` | `healthcheck` | Service health |
| `POST` | `/jobs` | `create_job` | Classified `JobRead` |
| `POST` | `/applications` | `create_application` | New application and creation event |
| `GET` | `/applications` | `list_applications` | Filtered, paginated applications |
| `PATCH` | `/applications/{id}/state` | `update_application_state` | Validated state transition |
| `POST` | `/applications/{id}/score` | `score_application` | Persisted deterministic score |
| `POST` | `/applications/{id}/policy-decisions` | `evaluate_application_policy` | Persisted policy decision |
| `POST` | `/applications/{id}/executor-actions/dry-run` | `dry_run_executor_action` | Persisted dry-run plan |
| `GET` | `/applications/{id}/events` | `list_application_events` | Append-only application events |
| `GET` | `/applications/{id}/audit` | `get_application_audit_summary` | Application, events, decisions, actions |

## Handler Behavior

### `create_job`

Passes `JobCreate` to the Tracker, which fills blank classifications with the deterministic
intake classifier. Returns HTTP 201.

### `create_application`

Requires an existing job. The Tracker creates an `ApplicationCreated` record and appends
`application.created`. Returns HTTP 201 or 404.

### `list_applications`

Supports optional state filtering plus `limit` and `offset`.

### `update_application_state`

Delegates transition validation to the Tracker. Generic state transitions use
`Tracker.update_state()`. Requests to move to `Submitted` use the guarded
`Tracker.submit_application()` workflow, which requires policy and executor evidence before
the state change. Invalid transitions return 400; missing applications return 404.

### `score_application`

Runs deterministic scoring against the linked job, persists score evidence, and appends
`application.scored`.

### `evaluate_application_policy`

Loads the application, derives the mode and policy context, evaluates policy, then records
the decision before any executor action. Returns HTTP 201.

### `_policy_context`

Uses explicit request context when provided. Otherwise it derives context from stored
application scoring and adds `application score` to missing data when no score exists.

### `dry_run_executor_action`

Requires a recorded, allowed policy decision for the same application. Dispatches only to
`StubExecutor` in `DRY_RUN` mode, creates executor request metadata at the API boundary,
then records the idempotent result and audit events.

### Audit Reads

`list_application_events` returns ordered events. `get_application_audit_summary` combines
the application, events, policy decisions, and executor actions for the dashboard.

## Transaction Boundary

Mutating handlers commit and refresh through `TrackerUnitOfWork`. Read handlers do not
commit. Domain and repository exceptions are translated to HTTP responses at the router.
