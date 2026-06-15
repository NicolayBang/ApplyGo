# M2 Packet Review Migration Sequencing Brief

**Status:** Proposed review brief
**Decision needed:** Migration sequencing for packet review persistence.
**Decision owners:** Nicolay + Francis
**Related:** `docs/contracts/database-schema-contract.md`; `docs/contracts/m2-application-packet-contract.md`

## Plain-English Decision

If M2 persists packet review decisions, how should the schema change be introduced without weakening
the M1 demo path or audit guarantees?

## Recommended Sequence

Use a single focused migration only after the packet persistence contract is approved.

Suggested steps:

1. Add `application_packet_reviews`.
2. Add deterministic check constraints for decision and source values.
3. Add indexes for `application_id` and `created_at`.
4. Choose restrictive or no-cascade foreign-key behavior based on the approved retention decision.
5. Add ORM model and relationship without delete cascade.
6. Add tracker and API behavior in the same implementation PR or a tightly paired follow-up.
7. Add PostgreSQL-backed tests for upgrade, insert, audit event, and retention behavior.

## Proposed Table Shape

```text
application_packet_reviews
id uuid PK
application_id uuid FK -> applications.id
decision varchar(32)
reviewed_by varchar(64)
source varchar(32)
packet_text text nullable
notes text nullable
created_at timestamptz
```

## Constraint Direction

Recommended decision constraint:

```text
decision IN ('approved', 'rejected', 'changes_requested')
```

Recommended source constraint:

```text
source IN ('dashboard')
```

These constraints keep M2 deterministic and prevent accidental expansion into unreviewed sources.

## Compatibility Requirements

The migration must preserve:

- existing `jobs`, `applications`, `policy_decisions`, `executor_actions`, and `event_log` data;
- current dashboard load and manual intake behavior;
- existing score, policy, dry-run, and submit-gate tests;
- M1 demo path without requiring packet review data.

## Validation Requirements

The implementation PR should run:

```text
alembic upgrade head
python -m pytest
python -m pytest tests/integration/test_seed_to_dashboard.py
```

If local PostgreSQL is unavailable, request Codespaces or GitHub-hosted validation before merge.

## Rollback Expectation

The migration should be reversible during development, but production rollback expectations can stay
out of M2 until deployment becomes real scope.

## Stop Conditions

Stop before implementation if the migration requires:

- changing existing application state values;
- changing policy or executor tables;
- changing event log retention;
- changing company identity or ADR-0005 timing;
- adding document versioning;
- adding external automation.
