# ADR-0002-canonical-data-model

## Status

Proposed

Approval requires Nicolay and Francis.

## Context

ApplyPilot M1 already has a seven-table SQLAlchemy and Alembic schema centered on
`applications`. It supports the current demo path but deliberately uses simple relationships:
company is stored on `jobs`, documents and email threads belong to one application, and executor
retry metadata is minimal.

The technical design review identified future requirements that the M1 shape cannot represent
cleanly:

- normalized companies and contacts
- immutable document versions reused by multiple applications
- recruiter threads related to multiple applications
- reusable screening answers
- separate packet, submission, and conversation lifecycles
- executor retry, backoff, and rate-limit metadata

These requirements are not part of the current M1 demo and must not be presented as implemented.

## Decision

### Current Baseline

Preserve the implemented M1 aggregate until a later migration is explicitly approved:

- `jobs`
- `applications`
- `documents`
- `email_threads`
- `policy_decisions`
- `executor_actions`
- `event_log`

`applications` remains the canonical M1 hub. Workflow owns state, PostgreSQL owns durable truth,
policy owns permission, and important decisions and execution results remain auditable.

### Proposed Future Model

Adopt the following as the proposed direction, not an implementation commitment:

| Phase | Proposed change |
|---|---|
| M3 intake normalization | Add `companies`; replace the job company string with an approved FK/backfill strategy |
| M5 packet model | Add `document_versions`, `application_documents`, `answer_library`, and `application_answers` |
| M7 recruiter email | Add `contacts`, `threads`, `messages`, and `thread_applications` |
| Later executor hardening | Add retry, backoff, and rate-limit fields; consider renaming actions to runs |

The future model uses explicit join tables for document-version/application and
thread/application many-to-many relationships.

### Change Control

- This ADR does not authorize migrations while its status is Proposed.
- Each phase requires a separate architecture review, deterministic Alembic migration, ORM update,
  runnable tests, documentation update, and PostgreSQL-backed validation.
- Table renames, lifecycle redesign, and audit retention changes must not be bundled silently with
  unrelated work.
- Current API compatibility and data backfill rules must be specified before each migration.

## Consequences

- The M1 schema remains small and demonstrable.
- Documentation can distinguish implemented truth from future design.
- Future normalization avoids premature tables while preserving an agreed direction.
- Later migrations must handle existing M1 data and may require temporary compatibility fields.
- Approval of this ADR alone does not approve every phase; it approves the direction and review
  boundaries.

## Supersedes

None.

## Superseded by

None.
