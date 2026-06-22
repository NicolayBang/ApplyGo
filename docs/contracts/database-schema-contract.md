# Database Schema Contract

**Status:** Implemented baseline plus M3 company identity cutover

**Scope:** PostgreSQL schema through migration `0011`

**Authority:** SQLAlchemy models and applied Alembic migrations

This contract describes the database shape that supports the implemented M1 demo:

```text
manual intake -> parse/classify -> state progression -> scoring
-> policy check -> dry-run executor -> audit timeline
```

It does not approve the future normalized data model in
`docs/decisions/ADR-0002-canonical-data-model.md`.

The implemented migration chain is
`0001 -> 0002 -> 0003 -> 0004 -> 0005 -> 0006 -> 0007 -> 0008 -> 0009 -> 0010 -> 0011`.

## Provisioning Boundary

`docker compose up -d postgres` starts an empty PostgreSQL server and a local named volume.
The schema is created and upgraded by running the one-shot migration service:

```bash
docker compose run --rm migrate
```

Developers may also run Alembic directly from `backend/`:

```bash
cd backend
python -m alembic upgrade head
```

The repository stores Compose configuration, ORM models, migrations, and seed/validation code.
It does not store the PostgreSQL image binary or a developer's database volume.

## Constraint Layers

- **Database constraint:** enforced by PostgreSQL for every writer.
- **ORM behavior:** enforced when writes and deletes pass through SQLAlchemy relationships.
- **Application validation:** enforced by API, Tracker, state machine, policy, or executor code.

An application enum or Pydantic rule is not a database constraint unless a migration creates a
PostgreSQL enum or `CHECK` constraint.

## Tables

### `jobs`

| Column | PostgreSQL type | Null | Default | Key / index |
|---|---|---:|---|---|
| `id` | `uuid` | no | supplied by ORM | PK |
| `source_url` | `varchar(2048)` | yes | none | |
| `raw_text` | `text` | yes | none | |
| `title` | `varchar(512)` | yes | none | |
| `company_source_text` | `varchar(256)` | yes | none | `ix_jobs_company_source_text` |
| `company_id` | `uuid` | no | none | FK -> `companies.id`, `ix_jobs_company_id` |
| `location` | `varchar(256)` | yes | none | |
| `remote_ok` | `boolean` | no | `false` | |
| `job_type` | `varchar(64)` | yes | none | |
| `ats_type` | `varchar(64)` | yes | none | |
| `salary_raw` | `varchar(256)` | yes | none | |
| `created_at` | `timestamptz` | no | `now()` | |
| `updated_at` | `timestamptz` | no | `now()` | |

The nullable intake fields are intentional for M1. `JobIntakeClassifier` may fill blank
classification fields before persistence, but PostgreSQL does not require them.

Migration `0010` backfills existing rows, and new job writes resolve or create a deterministic
company identity row and persist `company_id` in the same transaction. Migration `0011` completes
the M3 baseline cutover by requiring `company_id` and renaming the raw intake provenance field to
`company_source_text`.

API read models project the response `company` value from `companies.name` while exposing the raw
database/source value as `company_source_text`.

### `companies`

| Column | PostgreSQL type | Null | Default | Key / index |
|---|---|---:|---|---|
| `id` | `uuid` | no | supplied by ORM | PK |
| `name` | `varchar(256)` | no | none | `ck_companies_name_not_blank_m3` |
| `normalized_name` | `varchar(256)` | no | none | `ix_companies_normalized_name`, `ck_companies_normalized_name_not_blank_m3` |
| `domain` | `varchar(256)` | yes | none | |
| `normalized_domain` | `varchar(256)` | yes | none | `ix_companies_normalized_domain` |
| `created_at` | `timestamptz` | no | `now()` | |
| `updated_at` | `timestamptz` | no | `now()` | |

Unique indexes:

```text
uq_companies_normalized_domain_m3 on normalized_domain where normalized_domain is not null
uq_companies_normalized_name_without_domain_m3 on normalized_name where normalized_domain is null
```

`companies` owns canonical company identity for the implemented M3 baseline. The retained
`jobs.company_source_text` value is provenance and must not be treated as canonical company truth.

### `applications`

| Column | PostgreSQL type | Null | Default | Key / index |
|---|---|---:|---|---|
| `id` | `uuid` | no | supplied by ORM | PK |
| `job_id` | `uuid` | no | none | FK -> `jobs.id` (`ON DELETE CASCADE`), `ix_applications_job_id` |
| `state` | `varchar(64)` | no | `ApplicationCreated` | `ix_applications_state`, `ck_applications_state_m1` |
| `automation_mode` | `varchar(32)` | no | `manual` | `ck_applications_automation_mode_m1` |
| `fit_score` | `integer` | yes | none | |
| `confidence` | `varchar(16)` | yes | none | |
| `recommendation` | `varchar(32)` | yes | none | |
| `score_reasons` | `jsonb` | yes | none | |
| `score_risks` | `jsonb` | yes | none | |
| `missing_data` | `jsonb` | yes | none | |
| `red_flags` | `jsonb` | yes | none | |
| `created_at` | `timestamptz` | no | `now()` | |
| `updated_at` | `timestamptz` | no | `now()` | |

Migration `0004` and the ORM align the database default with the implemented state-machine value
`ApplicationCreated`. Migration `0006` enforces the stable M1 state and automation-mode vocabularies
with named PostgreSQL `CHECK` constraints.

### `documents` (M5 reusable logical library)

| Column | PostgreSQL type | Null | Default | Key / index |
|---|---|---:|---|---|
| `id` | `uuid` | no | supplied by ORM | PK |
| `doc_type` | `varchar(64)` | no | none | `ix_documents_doc_type`, `ck_documents_doc_type_m5` |
| `name` | `varchar(256)` | no | none | `ck_documents_name_not_blank_m5` |
| `is_archived` | `boolean` | no | `false` | `ix_documents_is_archived` |
| `created_at` | `timestamptz` | no | `now()` | |
| `updated_at` | `timestamptz` | no | `now()` | |

Migrations `0012`–`0014` implement the M5 reusable document library. A `documents` row is the stable
logical identity of a document and owns no content directly; it has no owning application. Migration
`0014` removed the legacy single-owner columns (`application_id`, `content`, `content_json`,
`version`) and the `ix_documents_application_id` index after the read-model API switched off them.
`ck_documents_doc_type_m5` enforces `doc_type IN ('resume','cover_letter','supporting','other')`.

### `document_versions` (immutable rendered versions)

| Column | PostgreSQL type | Null | Default | Key / index |
|---|---|---:|---|---|
| `id` | `uuid` | no | supplied by ORM | PK |
| `document_id` | `uuid` | no | none | FK -> `documents.id` (`ON DELETE RESTRICT`), `ix_document_versions_document_id` |
| `version_number` | `integer` | no | none | `ck_document_versions_version_positive_m5` |
| `content` | `text` | yes | none | |
| `content_json` | `jsonb` | yes | none | |
| `checksum` | `varchar(128)` | no | none | `ix_document_versions_checksum` |
| `created_at` | `timestamptz` | no | `now()` | |

Rows are immutable: there is no `updated_at` and no implemented path updates `content`,
`content_json`, `version_number`, or `checksum`. `uq_document_versions_document_id_version_number_m5`
makes `(document_id, version_number)` unique. `ck_document_versions_payload_present_m5` requires
`content IS NOT NULL OR content_json IS NOT NULL`. `ON DELETE RESTRICT` preserves version history.

### `application_documents` (append-only attachment of an exact version)

| Column | PostgreSQL type | Null | Default | Key / index |
|---|---|---:|---|---|
| `id` | `uuid` | no | supplied by ORM | PK |
| `application_id` | `uuid` | no | none | FK -> `applications.id` (`ON DELETE RESTRICT`), `ix_application_documents_application_id` |
| `document_version_id` | `uuid` | no | none | FK -> `document_versions.id` (`ON DELETE RESTRICT`), `ix_application_documents_document_version_id` |
| `role` | `varchar(64)` | no | none | `ck_application_documents_role_m5` |
| `display_order` | `integer` | no | none | `ck_application_documents_display_order_non_negative_m5` |
| `created_at` | `timestamptz` | no | `now()` | |

Append-only: attaching a newer version is a new row, never a silent upgrade.
`uq_application_documents_app_version_role_m5` makes `(application_id, document_version_id, role)`
unique. Both `ON DELETE RESTRICT` foreign keys preserve attachment history; no delete endpoint or
cascade removal exists.

### `answer_library` (current reusable answers)

| Column | PostgreSQL type | Null | Default | Key / index |
|---|---|---:|---|---|
| `id` | `uuid` | no | supplied by ORM | PK |
| `question_key` | `varchar(256)` | no | none | `ix_answer_library_question_key`, `ck_answer_library_question_key_not_blank_m5` |
| `question_text` | `text` | no | none | |
| `answer_text` | `text` | no | none | |
| `is_archived` | `boolean` | no | `false` | `ix_answer_library_is_archived` |
| `created_at` | `timestamptz` | no | `now()` | |
| `updated_at` | `timestamptz` | no | `now()` | |

Library answers are mutable (edit/archive in place). `uq_answer_library_question_key_active_m5`
enforces a single active row per `question_key` where `is_archived IS false`. Historical truth lives
only in immutable `application_answers` snapshots, never by mutating the library.

### `application_answers` (immutable answer snapshots)

| Column | PostgreSQL type | Null | Default | Key / index |
|---|---|---:|---|---|
| `id` | `uuid` | no | supplied by ORM | PK |
| `application_id` | `uuid` | no | none | FK -> `applications.id` (`ON DELETE RESTRICT`), `ix_application_answers_application_id` |
| `answer_library_id` | `uuid` | yes | none | FK -> `answer_library.id` (`ON DELETE RESTRICT`), `ix_application_answers_answer_library_id` |
| `question_key` | `varchar(256)` | no | none | `ck_application_answers_question_key_not_blank_m5` |
| `question_text` | `text` | no | none | |
| `answer_text` | `text` | no | none | |
| `created_at` | `timestamptz` | no | `now()` | |

A row is the immutable question/answer used by an application; a later edit or archive of the
referenced library row never changes this snapshot. `uq_application_answers_app_question_key_m5`
makes `(application_id, question_key)` unique. `ON DELETE RESTRICT` on `answer_library_id` preserves
provenance.

### `email_threads`

| Column | PostgreSQL type | Null | Default | Key / index |
|---|---|---:|---|---|
| `id` | `uuid` | no | supplied by ORM | PK |
| `application_id` | `uuid` | no | none | FK -> `applications.id` (`ON DELETE CASCADE`), `ix_email_threads_application_id` |
| `external_thread_id` | `varchar(256)` | yes | none | |
| `subject` | `varchar(512)` | yes | none | |
| `direction` | `varchar(16)` | no | `inbound` | `ck_email_threads_direction_m1` |
| `classification` | `varchar(64)` | yes | none | |
| `raw_body` | `text` | yes | none | |
| `draft_reply` | `text` | yes | none | |
| `sent_at` | `timestamptz` | yes | none | |
| `created_at` | `timestamptz` | no | `now()` | |

No Gmail integration is implemented in M1.

### `policy_decisions`

| Column | PostgreSQL type | Null | Default | Key / index |
|---|---|---:|---|---|
| `id` | `uuid` | no | supplied by domain | PK |
| `application_id` | `uuid` | no | none | FK -> `applications.id`, `ix_policy_decisions_application_id` |
| `action_type` | `varchar(64)` | no | none | |
| `mode` | `varchar(32)` | no | none | `ck_policy_decisions_mode_m1` |
| `decision` | `varchar(16)` | no | `review` | `ck_policy_decisions_decision_m1` |
| `allowed` | `boolean` | no | none | |
| `reasons` | `jsonb` | yes | none | |
| `risks` | `jsonb` | yes | none | |
| `required_overrides` | `jsonb` | yes | none | |
| `created_at` | `timestamptz` | no | `now()` | |

Mode and decision values are enforced by named PostgreSQL `CHECK` constraints. Migration `0007`
removes delete cascade so policy decisions remain durable audit-bearing records.

### `executor_actions`

| Column | PostgreSQL type | Null | Default | Key / index |
|---|---|---:|---|---|
| `id` | `uuid` | no | supplied by ORM | PK |
| `request_id` | `uuid` | no | generated at executor boundary | UNIQUE, `ix_executor_actions_request_id` |
| `application_id` | `uuid` | no | none | FK -> `applications.id`, `ix_executor_actions_application_id` |
| `worker` | `varchar(32)` | no | none | `ck_executor_actions_worker_m1` |
| `idempotency_key` | `varchar(256)` | no | none | UNIQUE, `ix_executor_actions_idempotency_key` |
| `action_type` | `varchar(64)` | no | none | |
| `execution_mode` | `varchar(16)` | no | none | `ck_executor_actions_execution_mode_m1` |
| `status` | `varchar(32)` | no | `queued` | `ck_executor_actions_status_m1` |
| `requested_by` | `varchar(64)` | no | none | |
| `requested_at` | `timestamptz` | no | generated at executor boundary | |
| `payload` | `jsonb` | yes | none | |
| `result` | `jsonb` | yes | none | |
| `created_at` | `timestamptz` | no | `now()` | |
| `completed_at` | `timestamptz` | yes | none | |

The unique idempotency key, request ID, worker vocabulary, execution mode, and status vocabulary are
database-enforced. The dry-run endpoint verifies an allowed, application-owned policy decision before
recording an action. Migration `0007` removes delete cascade so executor actions remain durable
audit-bearing records.

### `event_log`

| Column | PostgreSQL type | Null | Default | Key / index |
|---|---|---:|---|---|
| `id` | `uuid` | no | supplied by ORM | PK |
| `application_id` | `uuid` | no | none | FK -> `applications.id`, `ix_event_log_application_id` |
| `event_type` | `varchar(128)` | no | none | `ix_event_log_event_type` |
| `actor` | `varchar(64)` | no | `system` | |
| `from_state` | `varchar(64)` | yes | none | |
| `to_state` | `varchar(64)` | yes | none | |
| `payload` | `jsonb` | yes | none | |
| `created_at` | `timestamptz` | no | `now()` | `ix_event_log_created_at` |

Migration `0003` removes database `ON DELETE CASCADE`. The ORM relationship also avoids
delete/delete-orphan cascade and uses passive deletes. The repository exposes append and read
operations but no event update/delete API.

## Current Persistence Map

| Demo stage | Current write | Audit evidence |
|---|---|---|
| Manual intake / classification | `jobs` | none |
| Create application | `applications` | `application.created` |
| State progression | `applications.state` | `application.state_changed` |
| Scoring | score columns on `applications` | `application.scored` |
| Policy check | `policy_decisions` | `policy_decision_logged` |
| Dry-run executor | `executor_actions` | `executor_attempt_logged`, `executor_result_logged` |
| Packet review | `application_packet_reviews` | `application_packet.reviewed` |
| Audit timeline | read-only aggregate | ordered `event_log` rows plus policy/action records |

The current dry-run does not automatically advance application state after execution.

## Open Database Decisions

- The M5 document/answer model is **implemented**. Migrations `0012`–`0014` transformed the M1
  `documents` placeholder into the reusable logical library plus immutable `document_versions`,
  append-only `application_documents`, mutable `answer_library`, and immutable `application_answers`
  documented above, with a deterministic legacy backfill and a final cleanup that retired the legacy
  single-owner columns. See `docs/contracts/m5-packet-document-answer-contract.md` for the entity
  contract. ADR-0002 remains **Proposed** as the governing relational direction; the implemented
  tables prove the direction in code and migrations without implying the ADR was approved. Any
  remaining Nicolay/Francis sign-off on ADR-0002 is recorded as governance status only.
- The M7 normalized contacts/threads/messages model remains **Proposed / Not Implemented** under
  ADR-0002 and requires approval before adding tables.
- ADR-0005 records approved M3 company identity direction. Migration `0009` starts the
  compatibility schema, migration `0010` backfills legacy job rows, and migration `0011` completes
  the M3 baseline cutover by requiring `jobs.company_id` and renaming raw provenance to
  `jobs.company_source_text`. Later company merge UI, contacts, and external enrichment remain out
  of scope.
