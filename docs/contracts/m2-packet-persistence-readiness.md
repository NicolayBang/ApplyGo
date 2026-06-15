# M2 Packet Persistence Readiness Checklist

**Status:** Draft review checklist
**Milestone:** M2
**Authorizes implementation:** No

Use this checklist before starting any PR that persists packet review decisions.

## Required Decisions

- Confirm `application_packet_reviews` as a dedicated table, or choose an alternative.
- Confirm whether packet review rows should block application deletion or use database-level
  retention similar to policy/executor/event records.
- Confirm whether `packet_text` is stored in M2 or generated only at review time.
- Confirm allowed decision values: `approved`, `rejected`, `changes_requested`.
- Confirm the audit event name: `application_packet.reviewed`.

## Implementation Readiness

The implementation PR should be split only if needed, but the full implementation must cover:

- SQLAlchemy model and relationship.
- Alembic migration with deterministic constraints and indexes.
- Pydantic request/response schemas.
- Tracker method that writes the review row and appends the audit event in one unit of work.
- API endpoint for creating a packet review decision.
- Dashboard action only after backend behavior exists.
- Audit or review-summary exposure only if the UI needs it for the same milestone slice.

## Test Expectations

Runnable tests should prove:

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

Before merging the implementation PR, the reviewer should be able to answer:

- What decision was recorded?
- Who recorded it?
- Where is the audit evidence?
- What happens if the application is deleted?
- Does the feature preserve the M1 governed dry-run demo path?
