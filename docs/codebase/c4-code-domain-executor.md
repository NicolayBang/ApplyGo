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
| `action_type` | `str` | Structured action identifier |
| `mode` | `ExecutionMode` | Execute or dry-run |
| `application_id` | `str` | Target application |
| `idempotency_key` | `str` | Retry deduplication key |
| `payload` | `dict[str, Any]` | Action data and audit references |

### `ExecutorResult`

Contains a status string and a structured `details` dictionary.

## API Schemas

### `ExecutorDryRunRequest`

Requires a recorded `policy_decision_id`, action type, non-empty idempotency key, optional
payload, and actor.

### `ExecutorActionRead`

Returns the persisted executor action including execution mode, status, request payload,
result details, and timestamps.

## Enforcement

The dry-run endpoint verifies that:

1. The application exists.
2. The referenced policy decision exists and belongs to that application.
3. The recorded policy decision allows execution.
4. The executor result is persisted with attempt/result audit events.

`Tracker.record_executor_result()` reuses an existing action for the same idempotency key
and rejects a key already owned by another application.
