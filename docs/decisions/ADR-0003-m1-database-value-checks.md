# ADR-0003-m1-database-value-checks

| Field | Value |
|-------|-------|
| **Status** | Approved |
| **Date** | 2026-06-14 |
| **Owner** | Nicolay |
| **Reviewers required** | Nicolay + Francis |
| **Related** | `docs/contracts/database-schema-contract.md`; `docs/decisions/ADR-0002-canonical-data-model.md`; `docs/architecture/database-implementation-roadmap.md` |

## Context

M1 currently validates several enum-like values in application code, but PostgreSQL still accepts
any string for those columns. That is acceptable for the early spine, but it leaves the database
weaker than the architecture principle that the database owns truth.

The database roadmap identifies value checks as M1 hardening and recommends named PostgreSQL
`CHECK` constraints for small, stable value sets. PostgreSQL enum types are intentionally avoided
for M1 because they are more awkward to evolve when the workflow vocabulary changes.

This ADR decides the contract implemented by migration `0006_add_m1_value_check_constraints.py`.

## Decision

Adopt named PostgreSQL `CHECK` constraints for stable M1 value sets.

Migration `0006` adds constraints for:

| Table | Column | Allowed values |
|-------|--------|----------------|
| `applications` | `state` | `ApplicationCreated`, `Draft`, `ReadyForReview`, `Approved`, `Submitted`, `Rejected`, `Archived` |
| `applications` | `automation_mode` | `manual`, `dry_run`, `semi_auto`, `full_auto` |
| `policy_decisions` | `mode` | `manual`, `dry_run`, `semi_auto`, `full_auto` |
| `policy_decisions` | `decision` | `allow`, `deny`, `review` |
| `executor_actions` | `execution_mode` | `dry_run`, `execute` |
| `executor_actions` | `status` | `planned`, `queued`, `completed`, `failed`, `blocked`, `not_implemented` |
| `executor_actions` | `worker` | `email`, `browser`, `documents` |
| `email_threads` | `direction` | `inbound`, `outbound` |

Nullable scoring fields should not receive M1 database checks yet:

- `applications.confidence`
- `applications.recommendation`

Those values are still application-owned scoring outputs and can remain nullable while the scoring
model is being refined.

Constraint names should be stable and descriptive, for example:

```text
ck_applications_state_m1
ck_applications_automation_mode_m1
ck_policy_decisions_mode_m1
ck_policy_decisions_decision_m1
ck_executor_actions_execution_mode_m1
ck_executor_actions_status_m1
ck_executor_actions_worker_m1
ck_email_threads_direction_m1
```

The migration should be additive and reversible. It should not rename tables, add future lifecycle
columns, add executor retry fields, or change retention behavior.

## Implementation

Implemented by Alembic revision `0006_add_m1_value_check_constraints.py`.

The migration normalizes the legacy scaffold state value `discovered` to `ApplicationCreated`
before adding the state constraint, then creates all named M1 `CHECK` constraints. Downgrade drops
the same constraints in reverse order.

## Validation Required

The implementation PR must prove:

- `python -m alembic upgrade head` succeeds on a fresh PostgreSQL database.
- Existing M1 fixture/demo data survives the migration.
- Invalid writes are rejected by PostgreSQL for each constrained column.
- `python -m pytest` passes.
- The PostgreSQL-backed seed-to-dashboard test passes.

When local PostgreSQL is unavailable, delegate migration validation to Copilot or another
GitHub-hosted environment and record the result on the PR.

## Consequences

Positive:

- PostgreSQL begins enforcing the most important stable workflow and executor vocabularies.
- Bad direct writes fail before they can become dashboard or audit data.
- The next migration has a narrow, reviewable target.

Costs:

- Adding a new allowed value later requires a migration that updates the relevant `CHECK`
  constraint.
- The team must keep application enums, contracts, tests, and database constraints synchronized.

Not decided here:

- Policy/executor retention after application deletion.
- Soft-delete versus restrict-delete behavior.
- Future sub-lifecycle state columns.
- PostgreSQL enum types.

## Supersedes

None.

## Superseded by

None.
