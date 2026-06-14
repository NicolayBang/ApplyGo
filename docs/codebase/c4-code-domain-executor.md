# C4 Code Level: Executor Domain

## Overview

- **Location**: `backend/src/applypilot/domain/executor/`
- **Purpose**: Define the shared command/result contract and API schemas for executor work.
- **Milestone 1 behavior**: Only the dry-run API path is exposed; real worker dispatch is
  not implemented.

## Contracts

### `ExecutionMode`

| Member | Value |
|---|---|
| `EXECUTE` | `execute` |
| `DRY_RUN` | `dry_run` |

### `ExecutorRequest`

| Field | Type | Purpose |
|---|---|---|
| `request_id` | `UUID` | Unique command identifier carried through request/result/audit |
| `action_type` | `str` | Structured action identifier |
| `mode` | `ExecutionMode` | Execute or dry-run |
| `application_id` | `str` | Target application |
| `worker` | `str` | Executor worker slot, such as `email`, `browser`, or `documents` |
| `idempotency_key` | `str` | Retry deduplication key |
| `requested_by` | `str` | Actor or system component requesting the action |
| `requested_at` | `datetime` | Boundary timestamp for the command |
| `payload` | `dict[str, Any]` | Action data and audit references |

`ExecutorRequest.create()` generates the request ID and timestamp at the API or service
boundary so downstream workers and persistence receive the same command identity.

### `ExecutorResult`

Contains request identity, application ID, worker, execution mode, status, structured
`details`, optional error fields, and completion timestamp. The Tracker rejects executor
results whose metadata does not match the original request.

## API Schemas

### `ExecutorDryRunRequest`

Requires a recorded `policy_decision_id`, worker, action type, non-empty idempotency key,
optional payload, and actor.

### `ExecutorActionRead`

Returns the persisted executor action including request ID, worker, requested-by metadata,
execution mode, status, request payload, result details, and timestamps.

## Enforcement

The dry-run endpoint verifies that:

1. The application exists.
2. The referenced policy decision exists and belongs to that application.
3. The recorded policy decision allows execution.
4. The executor result is persisted with attempt/result audit events.

`Tracker.record_executor_result()` reuses an existing action for the same idempotency key
and rejects a key already owned by another application.
