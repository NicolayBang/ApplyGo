# Event Log Contract

## Purpose
Define append-only audit requirements for transitions, decisions, attempts, and results.

## Event Row Shape
```json
{
  "id": "uuid",
  "application_id": "uuid",
  "event_type": "string",
  "actor": "system|user|worker|policy",
  "from_state": "string|null",
  "to_state": "string|null",
  "payload": {},
  "created_at": "ISO-8601"
}
```

## Minimum Event Types
- `application.created`
- `application.state_changed`
- `application.scored`
- `policy_decision_logged`
- `executor_attempt_logged`
- `executor_result_logged`

Use the implemented `application.*` namespace for application lifecycle events.
Do not introduce aliases such as `state_transition` or `state_updated` unless an ADR
explicitly changes the event vocabulary and migration strategy.

## Ordering Requirements
Audit sequence for executor flow:
1. `policy_decision_logged`
2. `executor_attempt_logged`
3. `executor_result_logged`

If executor completion drives a later workflow state change, append that as a separate
`application.state_changed` event after the executor result. The current M1 dry-run flow
records the executor result without automatically submitting or otherwise advancing state.

## Immutability and Replay
- Event log is append-only; no in-place updates or deletes.
- Consumers must handle replay safely and idempotently.
- Event payloads should include idempotency and correlation identifiers.

## Milestone Note
Event schema and ordering describe implemented M1 behavior. Future event vocabulary changes
must update this contract, tests, dashboard labels, and any migration/backfill strategy in the same PR.
