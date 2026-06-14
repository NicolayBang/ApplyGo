# Executor Contract

## Purpose
Define one command contract for both dry-run and execute modes.

## Rule
Every executor-facing request uses the same payload shape. Only mode changes behavior.

## Request Schema
```json
{
  "request_id": "uuid",
  "application_id": "uuid",
  "worker": "email|browser|documents",
  "action_type": "string",
  "idempotency_key": "string",
  "mode": "dry_run|execute",
  "payload": {},
  "requested_by": "system|user|policy",
  "requested_at": "ISO-8601"
}
```

## Response Schema
```json
{
  "request_id": "uuid",
  "application_id": "uuid",
  "worker": "email|browser|documents",
  "mode": "dry_run|execute",
  "status": "planned|completed|failed|blocked",
  "result": {
    "side_effects": false,
    "requires": [],
    "planned_steps": []
  },
  "error_code": null,
  "error_message": null,
  "completed_at": "ISO-8601"
}
```

## Required Behaviors
- Enforce idempotency via `idempotency_key` before side effects.
- `dry_run` returns a plan-only result, lists required safeguards, and records no external side effects.
- `execute` performs the approved action.
- Log policy decision before call, and execution attempt/result after call.
- Return previous result when idempotency conflict indicates prior completion.

## Milestone Note
Workers remain stubs in Milestone 1; this contract is binding and implementation-ready.
