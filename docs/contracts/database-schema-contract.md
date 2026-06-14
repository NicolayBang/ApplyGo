# M1 Database Schema Contract

**Status:** Implemented baseline

**Scope:** Milestone 1 PostgreSQL schema

**Authority:** SQLAlchemy models and applied Alembic migrations

This contract describes the database shape that supports the implemented M1 demo:

```text
manual intake -> parse/classify -> state progression -> scoring
-> policy check -> dry-run executor -> audit timeline
```

It does not approve the future normalized data model in
`docs/decisions/ADR-0002-canonical-data-model.md`.

The implemented migration chain is `0001 -> 0002 -> 0003 -> 0004 -> 0005 -> 0006`.

## Provisioning Boundary

`docker compose up -d postgres` starts an empty PostgreSQL server and a local named volume.
It does not create ApplyPilot tables. The schema is created and upgraded by running:

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
| `company` | `varchar(256)` | yes | none | `ix_jobs_company` |
| `location` | `varchar(256)` | yes | none | |
| `remote_ok` | `boolean` | no | `false` | |
| `job_type` | `varchar(64)` | yes | none | |
| `ats_type` | `varchar(64)` | yes | none | |
| `salary_raw` | `varchar(256)` | yes | none | |
| `created_at` | `timestamptz` | no | `now()` | |
| `updated_at` | `timestamptz` | no | `now()` | |

The nullable intake fields are intentional for M1. `JobIntakeClassifier` may fill blank
classification fields before persistence, but PostgreSQL does not require them.

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

### `documents`

| Column | PostgreSQL type | Null | Default | Key / index |
|---|---|---:|---|---|
| `id` | `uuid` | no | supplied by ORM | PK |
| `application_id` | `uuid` | no | none | FK -> `applications.id` (`ON DELETE CASCADE`), `ix_documents_application_id` |
| `doc_type` | `varchar(64)` | no | none | |
| `content` | `text` | yes | none | |
| `content_json` | `jsonb` | yes | none | |
| `version` | `integer` | no | `1` | |
| `created_at` | `timestamptz` | no | `now()` | |

This is a placeholder M1 document model. Immutable document versions and cross-application reuse
are future work.

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
| `application_id` | `uuid` | no | none | FK -> `applications.id` (`ON DELETE CASCADE`), `ix_policy_decisions_application_id` |
| `action_type` | `varchar(64)` | no | none | |
| `mode` | `varchar(32)` | no | none | `ck_policy_decisions_mode_m1` |
| `decision` | `varchar(16)` | no | `review` | `ck_policy_decisions_decision_m1` |
| `allowed` | `boolean` | no | none | |
| `reasons` | `jsonb` | yes | none | |
| `risks` | `jsonb` | yes | none | |
| `required_overrides` | `jsonb` | yes | none | |
| `created_at` | `timestamptz` | no | `now()` | |

Mode and decision values are enforced by named PostgreSQL `CHECK` constraints. Current delete
behavior is application-owned cascade; whether decisions must outlive an application remains open.

### `executor_actions`

| Column | PostgreSQL type | Null | Default | Key / index |
|---|---|---:|---|---|
| `id` | `uuid` | no | supplied by ORM | PK |
| `request_id` | `uuid` | no | generated at executor boundary | UNIQUE, `ix_executor_actions_request_id` |
| `application_id` | `uuid` | no | none | FK -> `applications.id` (`ON DELETE CASCADE`), `ix_executor_actions_application_id` |
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
recording an action.

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

## M1 Persistence Map

| Demo stage | Current write | Audit evidence |
|---|---|---|
| Manual intake / classification | `jobs` | none |
| Create application | `applications` | `application.created` |
| State progression | `applications.state` | `application.state_changed` |
| Scoring | score columns on `applications` | `application.scored` |
| Policy check | `policy_decisions` | `policy_decision_logged` |
| Dry-run executor | `executor_actions` | `executor_attempt_logged`, `executor_result_logged` |
| Audit timeline | read-only aggregate | ordered `event_log` rows plus policy/action records |

The current dry-run does not automatically advance application state after execution.

## Open Database Decisions

- Decide whether to approve the proposed M1 retention contract in
  `docs/decisions/ADR-0004-m1-audit-retention.md`; today `policy_decisions` and
  `executor_actions` still cascade with application deletion.
- Decide whether Compose should gain a one-shot migration service; today migration is manual.
- Approve or reject the normalized future model through ADR-0002 before adding tables.
