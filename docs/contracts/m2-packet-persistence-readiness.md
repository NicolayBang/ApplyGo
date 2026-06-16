# M2 Packet Persistence Readiness Checklist

**Status:** Fulfilled for the implemented M2 baseline
**Milestone:** M2
**Authorizes implementation:** Historical guidance only

This checklist was used to shape the M2 packet review persistence implementation. Keep it as a
review reference for the implemented baseline and as a guardrail for future packet persistence
changes.

## Required Decisions

- Confirmed: `application_packet_reviews` is a dedicated table.
- Confirmed: packet review rows avoid ORM delete cascade and use reviewed database-level
  retention similar to policy/executor/event records.
- Confirmed: `packet_text` is nullable; the dashboard does not send full packet text by default.
- Confirmed allowed decision values: `approved`, `rejected`, `changes_requested`.
- Confirmed audit event name: `application_packet.reviewed`.

## Implementation Readiness

The implemented M2 baseline covers:

- SQLAlchemy model and relationship.
- Alembic migration with deterministic constraints and indexes.
- Pydantic request/response schemas.
- Tracker method that writes the review row and appends the audit event in one unit of work.
- API endpoint for creating a packet review decision.
- Dashboard action after backend behavior exists.
- Review-summary exposure for the latest packet review.

## Test Expectations

Runnable tests prove:

- valid review decisions persist;
- invalid decisions are rejected;
- missing applications return 404;
- audit event `application_packet.reviewed` is appended;
- packet review rows are queryable;
- migration upgrade succeeds on PostgreSQL;
- existing score, policy, dry-run, and dashboard asset tests still pass.

## Stop Conditions

Stop and request human review if implementation requires:

- changing policy permission behavior;
- changing executor behavior;
- changing application state transitions;
- adding document versioning;
- changing existing audit retention guarantees;
- introducing OpenClaw, Gmail sending, browser automation, or external side effects.

## Merge Gate

For the implemented M2 baseline, the reviewer should be able to answer:

- What decision was recorded?
- Who recorded it?
- Where is the audit evidence?
- What happens if the application is deleted?
- Does the feature preserve the M1 governed dry-run demo path?
