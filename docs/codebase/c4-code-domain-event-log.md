# C4 Code Level: Event Log

## Overview

- **Domain contract location**: `backend/src/applypilot/domain/event_log/`
- **Persistence location**: `backend/src/applypilot/db/models.py`
- **Write path**: `Tracker._append_event()`
- **Purpose**: Preserve ordered evidence of workflow-critical activity.

## `EventRecord`

`domain/event_log/models.py` defines a lightweight placeholder dataclass with:

- `id`
- `application_id`
- `event_type`
- `actor`
- `from_state`
- `to_state`
- `payload`
- `created_at`

The current Tracker writes ORM `EventLogEntry` instances directly; `EventRecord` is not yet
wired into that persistence path.

## `EventLogEntry`

The ORM record contains UUID, application UUID, event type, actor, optional from/to state,
JSON payload, and creation time. It has indexes for application, type, and creation time.

The event log is append-only by repository behavior: the Tracker exposes creation and read
operations but no event update or delete operation.

## Emitted Event Types

| Event type | Emitted by |
|---|---|
| `application.created` | `Tracker.create_application()` |
| `application.state_changed` | `Tracker.update_state()` |
| `application.scored` | `Tracker.score_application()` |
| `policy_decision_logged` | `Tracker.record_policy_decision()` |
| `executor_attempt_logged` | `Tracker.record_executor_result()` |
| `executor_result_logged` | `Tracker.record_executor_result()` |

Policy decisions are persisted before executor actions. Executor attempt and result evidence
is appended when a new idempotent action is recorded.
