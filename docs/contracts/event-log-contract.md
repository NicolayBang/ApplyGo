# Event Log Contract

## Purpose
Define append-only audit requirements for transitions, decisions, attempts, and results.

## Event Row Shape
```json
{
  "event_id": "uuid",
  "application_id": "uuid",
  "type": "string",
  "actor": "system|user|worker|policy",
  "payload": {},
  "created_at": "ISO-8601"
}
```

## Minimum Event Types
- `state_transition`
- `policy_decision_logged`
- `executor_attempt_logged`
- `executor_result_logged`
- `state_updated`

## Ordering Requirements
Audit sequence for executor flow:
1. `policy_decision_logged`
2. `executor_attempt_logged`
3. `executor_result_logged`
4. `state_updated`

## Immutability and Replay
- Event log is append-only; no in-place updates or deletes.
- Consumers must handle replay safely and idempotently.
- Event payloads should include idempotency and correlation identifiers.

## Milestone Note
Event schema and ordering are locked; implementation can start with minimal persistence scaffolding.