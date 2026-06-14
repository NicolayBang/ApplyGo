# C4 Code Level: Application State Machine

## Overview

- **Location**: `backend/src/applypilot/domain/state_machine/`
- **Purpose**: Define and enforce the implemented Milestone 1 application lifecycle.
- **Authority**: `ApplicationStateMachine` validates transitions; the Tracker persists accepted
  state changes and appends audit events.

## Code Elements

### `ApplicationState`

`states.py` defines seven string enum values:

| Member | Value |
|---|---|
| `APPLICATION_CREATED` | `ApplicationCreated` |
| `DRAFT` | `Draft` |
| `READY_FOR_REVIEW` | `ReadyForReview` |
| `APPROVED` | `Approved` |
| `SUBMITTED` | `Submitted` |
| `REJECTED` | `Rejected` |
| `ARCHIVED` | `Archived` |

### `ALLOWED_TRANSITIONS`

`transitions.py` contains the complete transition graph:

| Current state | Allowed next states |
|---|---|
| `ApplicationCreated` | `Draft` |
| `Draft` | `ReadyForReview`, `Archived` |
| `ReadyForReview` | `Approved`, `Rejected`, `Draft` |
| `Approved` | `Submitted`, `Rejected` |
| `Submitted` | `Archived` |
| `Rejected` | `Archived` |
| `Archived` | none |

### `InvalidStateTransitionError`

`service.py` defines the `ValueError` subtype raised when a requested transition is not
present in `ALLOWED_TRANSITIONS`.

### `ApplicationStateMachine`

| Method | Behavior |
|---|---|
| `can_transition(current, target)` | Returns whether the target is allowed. |
| `next_states(current)` | Returns a copy of the allowed target set. |
| `apply_transition(current, target)` | Returns the target or raises `InvalidStateTransitionError`. |

## Runtime Relationship

`Tracker.update_state()` converts persisted strings to `ApplicationState`, calls
`apply_transition()`, updates the application, and appends an
`application.state_changed` event. The API maps invalid transitions to HTTP 400.

## Tests

`backend/tests/unit/test_state_machine.py` covers the valid lifecycle path, rejection to
archive, invalid transition rejection, and terminal `Archived` behavior.
