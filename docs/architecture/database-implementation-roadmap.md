# Database Design and PostgreSQL Implementation Roadmap

**Status:** Planning and implementation guide

**Scope:** Implemented M1 database, next PostgreSQL work, and proposed later phases

**Does not authorize migrations:** Yes

This document reconciles the technical design drafts with the repository as it exists now. It is
an implementation-alignment guide, not a greenfield replacement for the current schema.

Authority remains:

1. `docs/architecture/OpenClaw_Final_Agreed_Architecture.pdf`
2. Approved ADRs
3. `docs/architecture/`
4. `docs/contracts/`
5. `AGENTS.md`

For exact implemented columns and constraints, use
`docs/contracts/database-schema-contract.md`. For the proposed direction, use
`docs/decisions/ADR-0002-canonical-data-model.md`. This roadmap does not override either document.

## Status Labels

- **DONE:** implemented and represented by models and migrations.
- **NEXT:** the next review or implementation step after human approval.
- **FUTURE:** planned for a later milestone and not implemented.
- **DECISION REQUIRED:** Nicolay and Francis must approve the contract before implementation.

## Executive Position

ApplyPilot already uses PostgreSQL. The current database is not merely mock data:

- Compose starts a real `postgres:16` server.
- Alembic migrations `0001` through `0007` create and harden the real M1 tables.
- SQLAlchemy writes persisted jobs, applications, policy decisions, executor actions, and events.
- The demo seed and seed-to-dashboard validator operate against PostgreSQL when it is running.

Compose now includes PostgreSQL/Redis health checks, a one-shot Alembic migration service, and an
optional profile-gated demo seed/validation service. Developers may still run Alembic directly from
`backend/` when they need manual control.

The repository does not contain the PostgreSQL image binary or a shared database volume. Docker
pulls `postgres:16`; each developer creates a local volume; Alembic reproduces the schema. A custom
PostgreSQL image is not needed for normal team sharing.

## Roadmap At A Glance

| Status | Milestone | Database shape |
|---|---|---|
| **DONE** | M1 | Seven-table application aggregate and migrations `0001`-`0007` |
| **DONE** | M1 hardening | Reproducible migration startup |
| **FUTURE** | M3 | Normalize companies and job ownership |
| **FUTURE** | M5 | Versioned application packets and reusable answers |
| **FUTURE** | M7 | Contacts, recruiter threads, and individual messages |
| **FUTURE** | Later executor hardening | Retry, backoff, rate-limit, and execution-attempt persistence |

Do not pull M3, M5, M7, or later executor work into an M1 hardening migration.

## DONE: Implemented M1 PostgreSQL Baseline

### Current tables

The implemented aggregate is:

1. `jobs`
2. `applications`
3. `documents`
4. `email_threads`
5. `policy_decisions`
6. `executor_actions`
7. `event_log`

`applications` is the central record. The current persistence path is:

```text
manual intake
-> jobs
-> applications
-> state and scoring fields
-> policy_decisions
-> executor_actions
-> event_log
-> dashboard audit view
```

### Current guarantees

- `applications.job_id` is a required foreign key.
- `executor_actions.idempotency_key` is unique in PostgreSQL.
- Application state changes pass through the state machine in application code.
- A policy decision is recorded before the current dry-run executor action.
- Executor attempts and results are represented in the event vocabulary.
- `event_log` has no database delete cascade from `applications`.
- The ORM does not delete or orphan-delete events when an application is removed.
- Migration `0004` aligns the application state default with `ApplicationCreated`.
- Migration `0006` enforces stable M1 value sets with named PostgreSQL `CHECK` constraints.
- Migration `0007` preserves policy decisions and executor actions by removing application delete cascade.

### Current limitations

- Company identity is normalized for the M3 deterministic baseline; contact ownership and company
  merge tooling remain future work.
- `documents` and `email_threads` are M1 placeholders with one application owner.
- Retry, backoff, and rate-limit fields are not present.

These are known boundaries, not evidence that the current schema is fake.

## NEXT: Contract Decisions Before Another Migration

The next database PR should not begin with a generated migration. It should begin with decisions
for the constraints and retention behavior that PostgreSQL will enforce.

### 1. Database value checks

**Status:** DONE BY ADR-0003 AND MIGRATION `0006`

Stable M1 values are enforced by named PostgreSQL `CHECK` constraints for:

- `applications.state`
- `applications.automation_mode`
- `email_threads.direction`
- `policy_decisions.mode`
- `policy_decisions.decision`
- `executor_actions.execution_mode`
- `executor_actions.status`
- `executor_actions.worker`

Nullable scoring outputs remain application-owned until their vocabulary stabilizes.

### 2. Policy and executor retention

**Status:** DONE BY ADR-0004 AND MIGRATION `0007`

Event rows, policy decisions, and executor actions are retained as audit-bearing records.

Choose one application deletion policy:

1. **Restrict physical deletion:** PostgreSQL rejects deletion while audit records reference the
   application.
2. **Soft-delete applications:** add deletion metadata and exclude deleted rows from normal reads.
3. **Retain detached audit records:** make selected foreign keys nullable and preserve snapshots.

M1 direction: restrict physical deletion and preserve events, policy decisions, and executor
records. Do not add soft-delete columns or detached audit records in M1.

### 3. PostgreSQL startup and migration ownership

**Status:** DONE

Today the operator runs:

```bash
docker compose up -d postgres redis
docker compose run --rm migrate
```

The migration service waits for healthy PostgreSQL, runs `alembic upgrade head`, and exits. The
optional `seed` service is profile-gated under `demo` and runs the seed-to-dashboard validation.
Neither service publishes a custom PostgreSQL image or bundles a FastAPI deployment.

### 4. Real PostgreSQL validation

**Status:** NEXT

Any implementation PR touching the schema must prove:

```bash
python -m ruff check .
python -m alembic upgrade head
python -m pytest
python -m scripts.validate_seed_to_dashboard
```

It must also show:

- a fresh empty database upgrades through every revision
- existing M1 fixture data survives the migration
- constraints reject invalid writes
- expected delete/retention behavior is enforced by PostgreSQL
- the API and dashboard still expose compatible fields

## Contract Readiness Register

The proposed ADR records direction, but direction alone is not enough to write safe migrations.
The following contracts are required before their related implementation begins.

### A. Current M1 schema contract

**Status:** DONE

**Location:** `docs/contracts/database-schema-contract.md`

It defines current columns, types, defaults, nullability, keys, indexes, uniqueness, delete
behavior, migration order, and demo persistence mapping.

This is the implementation baseline against which all future migrations are reviewed.

### B. Future schema contract

**Status:** FUTURE / REQUIRED BEFORE M3, M5, OR M7 MIGRATIONS

The future ER diagram is not a complete table contract. Before each milestone, define for every new
table:

- column name and PostgreSQL type
- nullability and server default
- primary, foreign, and candidate keys
- unique and partial unique indexes
- query indexes
- delete and update behavior
- ownership and cardinality
- mutable versus immutable fields
- timestamps and retention
- API-visible compatibility projections

This should be split by milestone rather than written as one permanently speculative mega-contract.

### C. Migration and compatibility contract

**Status:** APPROVED BASE DIRECTION / PROPOSED 3NF AMENDMENT / IMPLEMENTATION TIMING GATED

Every migration plan must define:

- starting schema revision and target revision
- data backfill algorithm
- treatment of blank, malformed, and duplicate legacy values
- temporary nullable columns or compatibility fields
- order of add, backfill, constrain, switch, and remove
- API compatibility during mixed application/database versions
- downgrade limits and rollback procedure
- row-count and referential-integrity checks
- zero-data-loss acceptance criteria

Table renames must use rename operations, not drop-and-recreate. Destructive column removal should
happen only after the replacement is populated and consumers have switched.

The approved-direction M3 company migration and compatibility boundary is recorded in
`docs/contracts/m3-company-migration-contract.md`.

Current review state: Nicolay and Francis approved the base M3 company identity direction. The
proposed 3NF completion amendment requires their approval and does not approve schema
implementation. Before any migration starts, the team must approve the amendment and confirm that
the active milestone is ready for company identity work.

### D. Company identity and deduplication contract

**Status:** IMPLEMENTED M3 BASELINE

The M3 baseline now uses `companies`, required `jobs.company_id`, and raw provenance in
`jobs.company_source_text`. Later company-related work still needs explicit review for:

- merge behavior when duplicate companies are discovered
- contact ownership
- recruiter/company relationship modeling
- external enrichment
- fuzzy matching or human merge workflows

The implemented migration shape is:

```text
add companies
-> insert deterministic Unknown Company
-> add nullable jobs.company_id
-> normalize and deduplicate legacy jobs.company values
-> create company rows
-> backfill jobs.company_id
-> validate all jobs have a company
-> switch canonical reads and writes to companies
-> make jobs.company_id non-null after approval
-> rename jobs.company to jobs.company_source_text
```

The M3 baseline is complete when migration `0011` is applied and validated: `companies` owns
canonical company facts, `jobs.company_id` is required, canonical display reads use
`companies.name`, and the retained raw source value is explicitly named `jobs.company_source_text`.

### E. Lifecycle and transition contract

**Status:** PARTLY DONE / FUTURE EXPANSION

The seven current M1 states are implemented:

```text
ApplicationCreated
Draft
ReadyForReview
Approved
Submitted
Rejected
Archived
```

Future design proposes independent lifecycle columns:

- `applications.lifecycle_state`
- `applications.packet_state`
- `applications.submission_state`
- `threads.conversation_state`

Before adding them, define:

- exact values and defaults
- allowed transitions
- terminal states
- actor or service allowed to trigger each transition
- required policy decision
- event emitted for success and failure
- compatibility mapping from current `applications.state`
- whether headline state is stored or derived

Do not rename `state` or add substates until this contract is approved. Fine-grained execution
status should not be forced into the headline workflow state.

### F. Audit and retention contract

**Status:** NEXT FOR M1 RETENTION; FUTURE FOR LONG-TERM POLICY

The contract must answer:

- which records are append-only
- which records may be corrected and how corrections are audited
- whether applications can be physically deleted
- how long events, decisions, actions, and payloads are retained
- whether personally identifiable data must be redacted separately from audit metadata
- who may read audit history
- what PostgreSQL foreign-key action applies to each relationship
- whether audit rows retain enough snapshot data if a parent changes

Minimum invariant:

```text
policy decision
-> decision audit evidence
-> executor attempt/result
-> result audit evidence
-> workflow state update
```

No deletion policy may silently erase proof that an action was permitted and attempted.

### G. M5 packet and answer contract

**Status:** FUTURE / M5

Proposed entities:

- `documents`
- `document_versions`
- `application_documents`
- `answer_library`
- `application_answers`

The contract must define:

- logical document identity versus immutable rendered version
- uniqueness and ordering of version numbers
- storage of text, structured content, artifact URI, checksum, and format
- application-document roles such as CV, cover letter, or attachment
- whether a document version may be reused across applications
- answer ownership, sensitivity, approval, versioning, and provenance
- deletion behavior for a version already used in an application

The required many-to-many relationship is:

```text
applications
<-> application_documents
<-> document_versions
```

The current M1 `documents.application_id` model remains in place until this M5 contract and its data
migration are approved.

### H. M7 recruiter communication contract

**Status:** FUTURE / M7

Proposed entities:

- `contacts`
- `threads`
- `messages`
- `thread_applications`

The contract must define:

- contact identity, company ownership, and deduplication
- provider and external message/thread identifiers
- inbound and outbound direction
- immutable raw message storage versus editable drafts
- sender, recipients, timestamps, and attachment references
- thread conversation state
- one thread relating to multiple applications
- Gmail synchronization and idempotency boundaries
- retention and privacy policy

The required many-to-many relationship is:

```text
applications
<-> thread_applications
<-> threads
```

The current M1 `email_threads.application_id` placeholder remains implemented until M7.

### I. Executor persistence contract

**Status:** PARTLY DONE / FUTURE HARDENING

DONE now:

- unique `idempotency_key`
- action type
- execute versus dry-run mode
- status
- request payload
- result payload
- created and completed timestamps

Future contract decisions:

- whether `executor_actions` is renamed to `executor_runs`
- attempt and maximum-attempt semantics
- retryable versus terminal failures
- deterministic backoff calculation
- `last_error` representation
- `next_retry_at`
- rate-limit key and scope
- one logical action versus multiple execution attempts
- result reuse for duplicate idempotency keys
- retention after application deletion

The future shape may include `attempt`, `max_attempts`, `rate_limit_key`, `last_error`, and
`next_retry_at`, but these fields should land with actual retry semantics and tests, not as unused
M1 columns.

### J. API and data compatibility contract

**Status:** APPROVED BASE DIRECTION / PROPOSED 3NF AMENDMENT / IMPLEMENTATION TIMING GATED

Database normalization must not unexpectedly break the current API or dashboard. Before a migration,
record:

- old request and response fields
- new database representation
- compatibility projection or adapter
- write behavior during the transition
- removal milestone for deprecated fields
- serialization of renamed states and tables
- error behavior for legacy values

The normalized company model may continue returning a `company` response string, but after cutover
that value is projected from `companies.name`. Raw intake text is separately exposed as
`company_source_text` where required. The compatibility period and owner must be explicit.

The approved-direction M3 company compatibility requirements are recorded in
`docs/contracts/m3-company-migration-contract.md`.

## Implementation Sequence Status

The M1 database decision, hardening, and reproducible migration-runner work described below is
complete. ADR-0003 and migration `0006` enforce stable values; ADR-0004 and migration `0007`
preserve audit-bearing records; the Compose `migrate` and optional `seed` services provide the
reproducible PostgreSQL path.

### PR 1: M1 database decision contracts — DONE

**Branch:** `docs/M1-database-hardening-contracts`

Completed decision work:

- ADR-0003 approved the database value-check policy and exact M1 constraints.
- ADR-0004 approved restrictive deletion for audit-bearing policy and executor records.
- The migration and rollback boundaries were recorded before implementation.

This decision stage changed no models or migrations.

### PR 2: M1 database hardening — DONE

**Branch:** `fix/M1-database-schema-hardening`

Completed implementation:

1. Migration `0004` aligned the application state default and ORM event retention behavior.
2. Migration `0005` added persisted executor contract metadata.
3. Migration `0006` added the approved M1 value constraints.
4. Migration `0007` removed delete cascades from policy and executor audit records.
5. SQLAlchemy models, PostgreSQL-backed tests, the schema contract, and the current ER view were
   aligned with the migration chain.

This work did not add `companies`, packet substates, recruiter entities, or executor retries.

### PR 3: Reproducible Compose migration runner — DONE

**Branch:** `feature/M1-compose-migration-runner`

Completed separately from schema hardening:

1. Added a supported-Python backend Dockerfile.
2. Added the PostgreSQL health check.
3. Added a one-shot `migrate` service.
4. Added a profile-gated demo seed service.
5. Documented startup, retry, failure, and cleanup behavior.

The canonical delivery remains migrations, not a database image or volume.

### Later milestone PRs

- M3: approved base company identity direction; proposed 3NF completion amendment, migration,
  ORM/API compatibility, and tests remain gated on Nicolay and Francis approval plus explicit
  implementation-timing approval.
- M5: packet/document/answer contract, migration, services, and tests.
- M7: contact/thread/message contract, migration, synchronization boundary, and tests.
- Later: executor attempt/retry/rate-limit contract, migration, scheduler behavior, and tests.

Each milestone receives its own ADR review or approved contract, migration commit, implementation
commits, tests, and documentation update.

## How The Team Shares PostgreSQL Work

### Canonical workflow

The repository shares:

- `docker-compose.yml`
- Alembic configuration and revisions
- SQLAlchemy models
- deterministic seed and validation code
- environment-variable examples

The developer runs:

```bash
git pull
cp .env.example .env
docker compose up -d postgres redis
docker compose run --rm migrate
cd backend
python -m scripts.validate_seed_to_dashboard
```

Docker pulls the official image and creates a local named volume. Alembic makes every teammate's
database structurally equivalent.

### What not to commit

Do not commit:

- PostgreSQL data directories or Docker volumes
- credentials or `.env`
- production or personal application data
- ad hoc SQL dumps as the authoritative schema
- a custom PostgreSQL image containing a developer database

A sanitized `pg_dump` may be used temporarily for troubleshooting or fixture creation, but it is
not the source of truth and must not contain secrets or personal data.

## Definition Of Ready For A PostgreSQL Schema PR

The implementation PR is ready to start only when:

- the target milestone is clear
- the relevant contract sections are approved
- every new or changed column is specified
- backfill and duplicate handling are specified
- API compatibility is specified
- deletion and retention behavior is specified
- migration and rollback boundaries are specified
- PostgreSQL-backed tests are planned
- Nicolay and Francis have approved architecture-critical decisions

## Definition Of Done

A PostgreSQL schema change is done when:

- migration from a fresh database succeeds
- migration from representative existing data succeeds
- SQLAlchemy and Alembic describe the same schema
- required constraints are database-enforced
- audit and deletion behavior are tested
- API/dashboard compatibility tests pass
- seed-to-dashboard validation passes
- implemented contracts and diagrams are updated
- CI is green
- Nicolay and Francis approve the high-risk change

Until those conditions are met on the implementation PR, the high-risk schema cutover must remain
unmerged.
