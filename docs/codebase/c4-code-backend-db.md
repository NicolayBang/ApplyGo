# C4 Code Level: Backend Database Layer

## Overview

- **Location**: `backend/src/applypilot/db/`
- **Technology**: SQLAlchemy with PostgreSQL-oriented UUID and JSONB models.
- **Purpose**: Own persisted truth through ORM models, request sessions, a unit of work, and
  the Tracker repository.

## Session and Dependency Boundary

### `session.py`

Creates a module-level SQLAlchemy engine from `Settings.database_url` and a `SessionLocal`
factory with autoflush and autocommit disabled.

### `TrackerUnitOfWork`

Wraps a request-scoped session and `Tracker`. Mutating API handlers explicitly call
`commit()` and `refresh()`.

### Dependencies

`get_session()` yields and closes a session. `get_tracker_unit()` yields a unit of work,
rolls back on exceptions, and always closes its session.

## ORM Models

| Model | Table | Role |
|---|---|---|
| `Job` | `jobs` | Normalized job source and classified metadata |
| `Application` | `applications` | Canonical workflow and scoring hub |
| `Document` | `documents` | Application-owned generated content placeholder |
| `EmailThread` | `email_threads` | Application-owned communication placeholder |
| `PolicyDecision` | `policy_decisions` | Recorded permission decision and evidence |
| `ExecutorAction` | `executor_actions` | Idempotent execution attempt/result record |
| `EventLogEntry` | `event_log` | Append-only audit event |

Operational child records cascade with the application. The event log foreign key does not
use database `ON DELETE CASCADE`, preserving the audit record at the schema boundary.

## `Tracker`

### Job and Application Methods

| Method | Behavior |
|---|---|
| `create_job` | Enriches blank metadata, inserts, and flushes a job |
| `get_job` | Fetches a job by UUID |
| `create_application` | Creates `ApplicationCreated` and appends `application.created` |
| `get_application` | Fetches an application by UUID |
| `list_applications` | Filters by optional state and applies pagination |
| `update_state` | Validates transition, persists it, appends `application.state_changed` |
| `score_application` | Scores linked job, stores evidence, appends `application.scored` |

### Policy and Executor Methods

| Method | Behavior |
|---|---|
| `record_policy_decision` | Persists permission evidence and appends policy audit event |
| `get_policy_decision` | Fetches one decision by UUID |
| `get_policy_decisions` | Returns ordered decisions for an application |
| `record_executor_result` | Enforces idempotency, persists action, appends attempt/result events |
| `get_executor_actions` | Returns ordered actions for an application |

### Event Methods

`_append_event()` is the internal append operation. `get_events()` returns an application's
events in creation order. No Tracker update or delete method is exposed for event rows.

## Relationships

The API depends on `TrackerUnitOfWork`; the unit of work owns the session and Tracker; the
Tracker coordinates domain validation and ORM persistence.
