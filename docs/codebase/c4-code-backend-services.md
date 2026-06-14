# C4 Code Level: Backend Services

## Overview

- **Location**: `backend/src/applypilot/services/`
- **Implemented service**: `StubExecutor`
- **Purpose**: Return an inspectable execution plan without external side effects.

## `StubExecutor`

### `dispatch(request: ExecutorRequest) -> ExecutorResult`

The method returns:

- `status="planned"` for `dry_run`
- `status="queued"` for `execute`

The structured `details` payload records:

- action type
- application ID
- idempotency key
- execution mode
- whether side effects are expected
- required safeguards
- planned steps
- associated policy decision ID

For dry-run, `side_effects` is false. The planned steps explicitly validate the recorded
policy decision, prepare the action payload, and record the executor result.

## Consumers

- `api.router.dry_run_executor_action()`
- `dev.demo_seed.seed_demo_application()`
- `tests.unit.test_executor_stub`

## Scope

The service does not call browser, email, or document workers. Those worker modules remain
**Not Implemented** placeholders in Milestone 1.
