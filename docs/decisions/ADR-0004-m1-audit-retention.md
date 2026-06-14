# ADR-0004-m1-audit-retention

| Field | Value |
|-------|-------|
| **Status** | Proposed |
| **Date** | 2026-06-14 |
| **Owner** | Nicolay |
| **Reviewers required** | Nicolay + Francis |
| **Related** | `docs/contracts/database-schema-contract.md`; `docs/decisions/ADR-0002-canonical-data-model.md`; `docs/architecture/database-implementation-roadmap.md`; `docs/architecture/current-data-model.md` |

## Context

ApplyPilot's core promise is governed automation with auditability. For M1, the event log already
survives application deletion at the database and ORM relationship layers. However,
`policy_decisions` and `executor_actions` still use `ON DELETE CASCADE` from `applications`.

That means a future physical application delete could remove the proof that an action was permitted,
attempted, and recorded. Even if no delete API exists today, the schema should not encode a deletion
rule that conflicts with the architecture principle that important decisions and executions must be
auditable.

This ADR decides the M1 retention contract before any migration changes foreign keys or ORM
relationships.

## Decision

Adopt restrictive physical deletion for M1 audit-bearing records.

For M1:

- `event_log` remains append-only and must not cascade-delete with applications.
- `policy_decisions` must not cascade-delete with applications.
- `executor_actions` must not cascade-delete with applications.
- PostgreSQL should reject physical deletion of an application while event, policy, or executor
  records reference it.
- SQLAlchemy relationships for event, policy, and executor records should avoid delete and
  delete-orphan cascade.
- No soft-delete columns are added in M1.
- No audit records are detached by nulling `application_id` in M1.

Generated or placeholder records may remain application-owned in M1:

- `documents`
- `email_threads`

Those tables do not yet represent binding permission or execution proof. Their long-term retention
belongs to later document and recruiter-communication contracts.

## Implementation Target

The next implementation PR should add one reversible Alembic migration that:

1. Drops the existing `ON DELETE CASCADE` foreign keys from `policy_decisions.application_id` and
   `executor_actions.application_id`.
2. Recreates both foreign keys without `ON DELETE CASCADE`.
3. Leaves `documents.application_id` and `email_threads.application_id` unchanged.
4. Leaves table names, columns, executor retry fields, and lifecycle state fields unchanged.

The matching SQLAlchemy model update should:

1. Remove delete/delete-orphan cascade from `Application.policy_decisions`.
2. Remove delete/delete-orphan cascade from `Application.executor_actions`.
3. Use passive deletes for retained audit-bearing relationships, consistent with `Application.events`.
4. Keep `Application.documents` and `Application.email_threads` application-owned for M1.

## Validation Required

The implementation PR must prove:

- `python -m alembic upgrade head` succeeds on a fresh PostgreSQL database.
- Downgrade restores the previous cascade behavior.
- Deleting an application with policy decisions is rejected by PostgreSQL.
- Deleting an application with executor actions is rejected by PostgreSQL.
- Deleting an application with event log rows remains rejected by PostgreSQL.
- ORM deletion does not silently delete policy decisions, executor actions, or event log rows.
- `python -m pytest` passes.
- The PostgreSQL-backed seed-to-dashboard test passes.

When local PostgreSQL is unavailable, delegate migration validation to Copilot or another
GitHub-hosted environment and record the result on the PR.

## Consequences

Positive:

- M1 audit evidence cannot be silently erased by deleting the application parent.
- Policy-before-executor evidence remains queryable as a database invariant.
- The migration target is narrow and reviewable.
- The decision supports the founding architecture without introducing future tables early.

Costs:

- Physical deletes of applications with audit evidence will fail.
- Any future admin delete workflow must explicitly choose soft-delete, redaction, or archival.
- Tests must distinguish generated placeholder records from audit-bearing records.

Not decided here:

- Long-term retention duration.
- PII redaction or privacy erasure workflow.
- Soft-delete columns.
- Document version retention after M5.
- Recruiter thread/message retention after M7.
- Executor retry/run history after later executor hardening.

## Supersedes

None.

## Superseded by

None.
