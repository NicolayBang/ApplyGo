# M5 Packet, Document, and Answer Contract

**Status:** Proposed / Not Implemented
**Milestone:** M5
**Authorizes migration:** No
**Authorizes implementation:** No

This contract proposes the M5 persistence foundation for versioned application documents, reusable
answers, and an application packet read model. It records *direction and detail* for a future schema.
It does **not** authorize any Alembic migration, ORM model, API handler, or frontend change.

Nicolay and Francis must explicitly approve this contract before any migration is authored or
merged. ADR-0002 remains Proposed; its M5 relational direction (Phase 2, contract G) must be
reaffirmed at this contract gate. If implementation would change ADR-0002's direction, a narrow M5
ADR is required and must be approved before schema work.

Authority order:

1. `docs/architecture/OpenClaw_Final_Agreed_Architecture.pdf`
2. approved ADRs in `docs/decisions/`
3. `docs/architecture/`
4. `docs/contracts/`
5. `AGENTS.md`

Related documents:

- `docs/decisions/ADR-0002-canonical-data-model.md` (Proposed direction, Phase 2 / contract G)
- `docs/architecture/database-implementation-roadmap.md` (contract G — M5 packet and answer)
- `docs/contracts/database-schema-contract.md` (implemented baseline through migration `0011`)
- `docs/contracts/m2-application-packet-contract.md` (implemented review-only packet boundary)
- `docs/contracts/m2-packet-persistence-contract.md` (implemented `application_packet_reviews`)
- `docs/contracts/http-api-contract.md` (implemented HTTP boundary plus Proposed M5 API section)

## Why This Contract Exists

The implemented baseline stores a single-application-owner `documents` placeholder and persists
human packet-review decisions in `application_packet_reviews`. That is enough for the local M2
review slice, but it cannot express the M5 architecture outcome: a tailored document version that is
authored once, frozen, and reused across applications, plus reusable screening answers whose
historical use must never be silently rewritten.

This contract defines the durable, versioned, audit-preserving shape that M5 needs, while keeping the
implemented M1/M2/M3/M4 behavior intact.

## Scope Boundaries

In scope (proposed, not implemented):

- a reusable logical document library (`documents`);
- immutable rendered document versions (`document_versions`);
- an append-only application-to-version attachment table (`application_documents`);
- a reusable answer library (`answer_library`);
- immutable per-application answer snapshots (`application_answers`);
- an application packet read model that projects exact attached versions, answer snapshots, and the
  current M2 review evidence;
- the additive migration path that converts the legacy placeholder without data loss.

Out of scope for M5:

- authentication, `user_id`, accounts, or multi-tenant fields. M5 remains a single workspace until an
  approved authentication milestone. Do not add speculative `user_id` or tenancy columns.
- recruiter contacts, threads, or messages (M7, contract H);
- Gmail, browser automation, real submission, or any external side effect;
- executor retry/backoff/rate-limit hardening (Phase 4, contract I);
- policy, executor, or application-state transition changes;
- LLM-required happy paths;
- any delete endpoint or destructive cascade.

## Single-Workspace Assumption

M5 is a single-operator workspace. Documents, versions, and answers are workspace-global reusable
records, not owned by an account. When an approved authentication milestone exists, ownership and
tenancy will be defined in that milestone's contract. This contract must not pre-add `user_id`,
`owner_id`, `account_id`, or tenancy keys.

## Entities

All tables below are **Proposed / Not Implemented**. Types are PostgreSQL types. The migration that
introduces them starts from implemented revision `0011` (first new revision `0012`). Every `id` is a
UUID supplied by the ORM. Every `created_at`/`updated_at` is `timestamptz` defaulting to `now()`.

### Proposed / Not Implemented: `documents` (reusable logical document library)

The implemented placeholder `documents` table is transformed into the reusable logical document
library. A `documents` row is the stable logical identity of a document; it owns no content directly.
Content lives only in immutable `document_versions` rows.

| Column | PostgreSQL type | Null | Default | Key / index |
|---|---|---:|---|---|
| `id` | `uuid` | no | supplied by ORM | PK |
| `doc_type` | `varchar(64)` | no | none | `ck_documents_doc_type_m5`, `ix_documents_doc_type` |
| `name` | `varchar(256)` | no | none | `ck_documents_name_not_blank_m5` |
| `is_archived` | `boolean` | no | `false` | `ix_documents_is_archived` |
| `created_at` | `timestamptz` | no | `now()` | |
| `updated_at` | `timestamptz` | no | `now()` | |

Rules:

- `doc_type` is validated by a named PostgreSQL `CHECK` constraint to one of:
  `resume`, `cover_letter`, `supporting`, `other`.
- `name` must be non-blank (database `CHECK`), and is a human-facing label only.
- `is_archived` hides a document from default library reads without deleting it. Archived documents
  remain attachable-history truth and remain readable through history projections.
- A `documents` row never stores content, version numbers, or application ownership.

### Proposed / Not Implemented: `document_versions` (immutable rendered versions)

A `document_versions` row is a frozen, immutable rendering of one logical document. It is never
updated after insert.

| Column | PostgreSQL type | Null | Default | Key / index |
|---|---|---:|---|---|
| `id` | `uuid` | no | supplied by ORM | PK |
| `document_id` | `uuid` | no | none | FK -> `documents.id` (`ON DELETE RESTRICT`), `ix_document_versions_document_id` |
| `version_number` | `integer` | no | none | `ck_document_versions_version_positive_m5` |
| `content` | `text` | yes | none | |
| `content_json` | `jsonb` | yes | none | |
| `checksum` | `varchar(128)` | no | none | `ix_document_versions_checksum` |
| `created_at` | `timestamptz` | no | `now()` | |

Rules:

- `version_number` is a positive integer (`CHECK version_number > 0`) and is unique per document:
  `uq_document_versions_document_id_version_number_m5 on (document_id, version_number)`.
- Version numbers are assigned sequentially per document; numbering is per-document, not global.
- At least one payload is required by a database `CHECK`:
  `ck_document_versions_payload_present_m5` requires `content IS NOT NULL OR content_json IS NOT NULL`.
- `checksum` is a deterministic content checksum used to detect accidental duplicate renders and to
  support integrity verification. It is not a security signature.
- Rows are immutable: no `updated_at`, and no implemented path updates `content`, `content_json`,
  `version_number`, or `checksum` after insert. Corrections create a new version, never an in-place
  edit.
- `ON DELETE RESTRICT` to `documents` prevents deleting a logical document while versions exist.

### Proposed / Not Implemented: `application_documents` (append-only attachment of an exact version)

Attaches one exact `document_versions` row to one `applications` row. This is the document side of
the document↔application many-to-many relationship in ADR-0002.

| Column | PostgreSQL type | Null | Default | Key / index |
|---|---|---:|---|---|
| `id` | `uuid` | no | supplied by ORM | PK |
| `application_id` | `uuid` | no | none | FK -> `applications.id` (`ON DELETE RESTRICT`), `ix_application_documents_application_id` |
| `document_version_id` | `uuid` | no | none | FK -> `document_versions.id` (`ON DELETE RESTRICT`), `ix_application_documents_document_version_id` |
| `role` | `varchar(64)` | no | none | `ck_application_documents_role_m5` |
| `display_order` | `integer` | no | none | `ck_application_documents_display_order_non_negative_m5` |
| `created_at` | `timestamptz` | no | `now()` | |

Rules:

- An attachment binds an **exact** `document_version_id`. It never silently upgrades to a later
  version. Attaching a newer version is a new, explicit `application_documents` row.
- `role` is validated by a named `CHECK` to one of: `resume`, `cover_letter`, `supporting`, `other`.
  An application may have multiple attachments through distinct roles and ordering.
- `display_order` is a non-negative integer giving a deterministic, stable ordering of attachments
  for a single application. Reads must order by `display_order`, then `created_at`, then `id` so the
  projection is deterministic.
- Uniqueness prevents duplicate identical links:
  `uq_application_documents_app_version_role_m5 on (application_id, document_version_id, role)`.
- The table is append-only. Replacing an attachment is modeled as a new row; M5 authorizes no delete
  endpoint and no cascade removal of attachment rows.
- `ON DELETE RESTRICT` on both foreign keys preserves the historical fact that a specific version was
  attached to a specific application.

### Proposed / Not Implemented: `answer_library` (current reusable answers)

Stores the current, reusable question/answer record. Unlike document versions, library answers are
mutable: the *current* reusable answer may be edited or archived. Historical truth is preserved
separately in `application_answers`, never by mutating the library.

| Column | PostgreSQL type | Null | Default | Key / index |
|---|---|---:|---|---|
| `id` | `uuid` | no | supplied by ORM | PK |
| `question_key` | `varchar(256)` | no | none | `ix_answer_library_question_key`, `ck_answer_library_question_key_not_blank_m5` |
| `question_text` | `text` | no | none | |
| `answer_text` | `text` | no | none | |
| `is_archived` | `boolean` | no | `false` | `ix_answer_library_is_archived` |
| `created_at` | `timestamptz` | no | `now()` | |
| `updated_at` | `timestamptz` | no | `now()` | |

Rules:

- `question_key` is a stable lookup key and must be non-blank. Active uniqueness is enforced by a
  partial unique index over non-archived rows:
  `uq_answer_library_question_key_active_m5 on (question_key) where is_archived is false`.
  Archiving frees the key for a future active answer while preserving the archived row.
- `answer_text` and `question_text` may be updated in place; `updated_at` advances on edit.
- Archiving (`is_archived = true`) removes the answer from default library reads but never deletes it
  and never alters any `application_answers` snapshot.

### Proposed / Not Implemented: `application_answers` (immutable answer snapshots)

Stores the immutable question-and-answer snapshot actually used by an application, with optional
provenance back to the library record it was sourced from.

| Column | PostgreSQL type | Null | Default | Key / index |
|---|---|---:|---|---|
| `id` | `uuid` | no | supplied by ORM | PK |
| `application_id` | `uuid` | no | none | FK -> `applications.id` (`ON DELETE RESTRICT`), `ix_application_answers_application_id` |
| `answer_library_id` | `uuid` | yes | none | FK -> `answer_library.id` (`ON DELETE RESTRICT`), `ix_application_answers_answer_library_id` |
| `question_key` | `varchar(256)` | no | none | `ck_application_answers_question_key_not_blank_m5` |
| `question_text` | `text` | no | none | |
| `answer_text` | `text` | no | none | |
| `created_at` | `timestamptz` | no | `now()` | |

Rules:

- A row is an immutable snapshot of the exact question and answer at the moment it was attached to the
  application. No implemented path updates `question_text` or `answer_text` after insert.
- `answer_library_id` is optional provenance. A later edit or archive of the referenced library row
  never changes the snapshot's `question_text` or `answer_text`. Historical application truth is owned
  by `application_answers`, not by `answer_library`.
- `ON DELETE RESTRICT` on `answer_library_id` preserves provenance: a library row that has been used
  by an application cannot be physically deleted.
- Deterministic per-application uniqueness of a snapshot key:
  `uq_application_answers_app_question_key_m5 on (application_id, question_key)`.

## Proposed / Not Implemented Deletion, Archive, and Retention

- This proposal defines **no delete endpoint** and **no destructive cascade**. There is no API or ORM path
  that removes documents, versions, attachments, library answers, or answer snapshots.
- Library-style records (`documents`, `answer_library`) support **archive**, not delete. Archiving is
  a boolean state change that hides records from default reads while preserving them.
- Physical deletion is **restricted** by `ON DELETE RESTRICT` foreign keys wherever a historical
  application record references a document version or library answer. PostgreSQL must reject deletion
  while history references exist.
- Immutable records (`document_versions`, `application_documents`, `application_answers`) are
  append-only audit-bearing truth and are never edited in place.
- The `event_log` remains the append-only audit source; M5 adds no delete/update path to it.

## Proposed / Not Implemented Audit Events

M5 attachment and answer activity must append audit events that contain identifiers and metadata
only — never full document or answer content. Candidate event names follow the implemented
`noun.verb` vocabulary style and must not be added until implementation exists:

```text
application_document.attached
application_answer.recorded
```

Allowed payload fields (identifiers and metadata only):

```json
{
  "application_id": "uuid",
  "application_document_id": "uuid",
  "document_version_id": "uuid",
  "role": "resume|cover_letter|supporting|other",
  "version_number": 1,
  "actor": "string",
  "created_at": "datetime"
}
```

```json
{
  "application_id": "uuid",
  "application_answer_id": "uuid",
  "answer_library_id": "uuid|null",
  "question_key": "string",
  "actor": "string",
  "created_at": "datetime"
}
```

Audit payloads must never include `content`, `content_json`, `answer_text`, or `question_text`. Full
content lives only on the immutable rows themselves.

## Proposed / Not Implemented Response Projections

The packet read model projects exact attached versions and answer snapshots together with the
current implemented M2 review evidence. It must:

- project the exact `version_number`, `checksum`, `role`, and `display_order` for each attached
  document, ordered deterministically;
- project answer snapshots from `application_answers`, never re-derived from the mutable library;
- include the latest packet review from the implemented `application_packet_reviews` evidence so the
  packet read model reuses, and does not replace, the M2 review boundary;
- remain additive: existing implemented response fields and the dashboard types in
  `frontend/app/src/api/types.ts` must continue to work unchanged.

The exact HTTP request/response shapes and error behavior are specified in the Proposed M5 API —
Not Implemented section of `docs/contracts/http-api-contract.md`.

## Proposed / Not Implemented Future Additive Migration Path

The migration is additive, deterministic, and must preserve every existing `documents` row. It starts
from implemented revision `0011`. No step below is authorized until this contract is approved.

1. **Add schema.** Alter the existing `documents` table in place to add the logical-library fields,
   retaining its legacy single-owner columns during compatibility, and create the other M5 tables and
   constraints. Introduce the reusable shape alongside the existing placeholder data rather than
   dropping and recreating the table.
2. **Deterministic legacy-document backfill.** For every existing placeholder `documents` row
   (currently `application_id`-owned with `doc_type`, `content`, `content_json`, `version`), create a
   logical document, an initial immutable `document_versions` row carrying the existing content and a
   computed checksum, and an `application_documents` attachment that binds the original application to
   that exact version with a deterministic `role` and `display_order`. A legacy row with both content
   fields null becomes an explicitly empty initial version (`content = ''`) with the checksum of that
   empty value; it is not dropped or silently given generated content. The backfill must be
   reproducible and idempotent.
3. **Validate preservation.** Prove row-count and referential-integrity preservation: every legacy
   document is represented by exactly one logical document, one initial version, and one attachment;
   no content is lost; checksums match the migrated content; existing `application_packet_reviews`
   rows are untouched.
4. **Switch readers.** Move API/service reads to the new tables and the packet read model while
   keeping responses compatible with the dashboard. Maintain compatibility during any mixed
   application/database window.
5. **Remove legacy fields/cascade only after compatibility checks.** Remove the legacy
   single-owner columns and the `documents.application_id` cascade behavior only after readers have
   switched and compatibility checks pass. Use rename/alter operations, never drop-and-recreate, and
   never remove a column before its replacement is populated and consumers have switched.

Each migration must prove, per ADR-0002 and the database implementation roadmap:

- a fresh empty database upgrades through every revision, including a fresh upgrade from `0011`;
- representative legacy `documents` data survives with no loss;
- constraints reject invalid writes (blank name, non-positive version, missing payload, duplicate
  active answer key, invalid `doc_type`/`role`);
- `ON DELETE RESTRICT` deletion/retention behavior is database-enforced;
- API and dashboard compatibility holds;
- `ruff`, `pytest`, and `validate_seed_to_dashboard` pass.

## Proposed / Not Implemented Validation Requirements For A Future Implementation PR

Any implementation PR (PR 2 and later) must include runnable PostgreSQL-backed tests for:

- valid document/version/attachment/answer writes;
- immutable-version enforcement (no in-place edit of `document_versions` or `application_answers`);
- positive version numbering and per-document uniqueness;
- payload-present rule on `document_versions`;
- attachment binds an exact version and never auto-upgrades;
- deterministic attachment ordering in the packet projection;
- active answer-key uniqueness and archive behavior;
- answer-snapshot immutability when the library answer is later edited or archived;
- restricted deletion when history references a version or library answer;
- audit events carry identifiers/metadata only, never content;
- fresh upgrade from `0011` and representative legacy-data preservation;
- API/dashboard compatibility and seed-to-dashboard validation.

## Proposed / Not Implemented Review Rule

This contract is Proposed / Not Implemented. No migration, ORM model, API handler, frontend change,
delete endpoint, or cascade behavior is authorized by this document. Stop and obtain explicit Nicolay
and Francis approval, and reaffirm ADR-0002's M5 direction, before any M5 schema work begins.
