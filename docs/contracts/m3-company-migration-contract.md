# M3 Company Migration Contract

**Status:** Approved direction; proposed 3NF amendment pending review; implementation timing gated

**Scope:** Future M3 migration from `jobs.company` text to first-class company identity

**Authority:** Approved M3 direction contract; does not authorize migration until timing is approved

**Review state:** Existing direction approved; 3NF completion amendment and later implementation
timing require Nicolay and Francis approval

**Related:** `docs/decisions/ADR-0005-m3-company-identity.md`,
`docs/contracts/database-schema-contract.md`, `docs/architecture/database-implementation-roadmap.md`

This contract defines the safety boundary for the future M3 company identity migration. It is not an
implemented schema description. The current M1 source of truth remains `jobs.company` until an
approved migration changes the database, ORM, API, dashboard, tests, and documentation together.

Nicolay and Francis approved the existing direction for M3, but the proposed 3NF completion
requirements in this revision are not yet approved and implementation remains gated. Before any
schema migration starts, the team must approve this amendment and explicitly confirm that the
current milestone is ready for company identity work.

Do not implement yet unless the implementation PR is limited to deterministic company identity,
preserves `jobs.company`, avoids source-url domain assumptions, includes placeholder handling, and
proves PostgreSQL migration plus API/dashboard compatibility.

## Starting Point

The implemented M1 schema stores company display text directly on `jobs.company`.

Current behavior that must remain compatible during the M3 transition:

- manual intake can create a job without a company
- dashboard/API consumers can read a displayable `company` value
- existing jobs and applications survive migration without data loss
- M1 audit records remain unchanged

## Target Shape

The future M3 migration may add:

```text
companies
jobs.company_id -> companies.id
```

The migration must preserve `jobs.company` as source/provenance text during backfill. The completed
M3 shape must use required `jobs.company_id` for canonical identity and rename the legacy column to
`jobs.company_source_text`.

## Target Normal Form

M3 company normalization targets a practical 3NF ownership boundary. This includes 1NF and 2NF;
the retained atomic source text has a distinct provenance meaning rather than duplicating canonical
company truth.

- `companies` is the sole owner of canonical company name, domain, and normalized identity.
- `jobs` stores `company_id` plus job-owned attributes and raw `company_source_text` provenance.
- Canonical company reads join through `jobs.company_id`; source text is never canonical fallback.
- Company-owned facts must not be copied onto `jobs`.
- Materialized normalized keys are controlled company attributes calculated by one deterministic
  normalization implementation. They are the only documented denormalization exception and exist
  for matching and indexing.

## Backfill Rules

Backfill must be deterministic:

- Blank or whitespace-only `jobs.company` values map to a seeded `Unknown Company` row.
- Clearly confidential employer text maps to a seeded `Confidential Company` row.
- Non-blank company values with the same normalized non-null domain map to the same company.
- Non-blank company values without a domain deduplicate only by exact `normalized_name`.
- `jobs.source_url` must not be used to infer employer domain or company identity. It may identify
  an ATS, job board, or redirect host rather than the employer.
- Fuzzy matching, AI matching, and external enrichment are out of scope for the migration.
- Original `jobs.company` text is not overwritten during backfill.

## Migration Order

The implementation PR should use an add/backfill/constrain sequence:

1. Add `companies` with nullable domain fields and deterministic timestamps.
2. Seed `Unknown Company` and `Confidential Company`.
3. Add nullable `jobs.company_id`.
4. Backfill `jobs.company_id` from existing `jobs.company`.
5. Add indexes and uniqueness constraints after backfill is valid.
6. Verify every existing job has a company mapping.
7. Switch canonical reads and writes to the company relationship.
8. Make `jobs.company_id` non-null after validation and human approval.
9. Rename `jobs.company` to `jobs.company_source_text` after API/dashboard consumers no longer
   depend on the database column name.

## API And Dashboard Compatibility

During the compatibility period:

- API responses must continue exposing a display `company` string for existing consumers, projected
  from `companies.name` after cutover.
- Dashboard rows must keep showing company text without requiring frontend rewrites in the same PR.
- An additive `company_source_text` field may expose raw intake provenance where needed.
- New writes must deterministically create or reuse a company and persist `company_id` in the same
  transaction.
- Compatibility may span multiple M3 migrations, but M3 is not complete while `jobs.company` remains
  an ambiguous canonical-looking column.

## Validation Requirements

The implementation PR must include runnable validation for:

- fresh PostgreSQL upgrade through the full Alembic chain
- representative existing M1 data surviving the migration
- blank company backfill to `Unknown Company`
- confidential company backfill to `Confidential Company`
- same normalized domain sharing one company row
- no-domain exact-name deduplication
- API/dashboard compatibility for existing company display fields
- PostgreSQL constraints and indexes
- final non-null `jobs.company_id`
- canonical API reads from `companies.name`
- provenance preserved in `jobs.company_source_text`
- rejection of writes that omit the resolved company relationship after cutover
- absence of company-owned attributes on `jobs`
- full backend pytest suite
- seed-to-dashboard validation against PostgreSQL

When local PostgreSQL is unavailable, request Remote Validation Assist and record the result in the
PR.

## Implementation Entry Conditions

An implementation PR is allowed only after the team explicitly confirms timing. That PR must remain
limited to:

- deterministic company identity migration;
- preserving legacy `jobs.company` values as provenance during migration;
- establishing `companies` as the only canonical owner of company facts;
- completing the cutover to required `jobs.company_id` and `jobs.company_source_text`;
- explicit `Unknown Company` and `Confidential Company` placeholder handling;
- no source-url domain assumptions;
- PostgreSQL migration, backfill, and constraint validation;
- API and dashboard compatibility for existing company display behavior.

## Approval Checklist

Before this contract is implemented, Nicolay and Francis should confirm:

- Backfill may create `Unknown Company` and `Confidential Company` rows.
- The migration preserves original `jobs.company` text.
- The completed M3 schema renames that provenance field to `company_source_text`.
- No fuzzy matching, AI matching, or external enrichment runs during backfill.
- API and dashboard compatibility for the existing company display field is required in the same
  implementation PR.
- Making `jobs.company_id` non-null requires validation evidence and explicit human approval and is
  required before M3 company normalization is complete.
- Downgrade limits and backup expectations are documented in the implementation PR.

## Rollback Boundary

Downgrade support must not silently discard company identity data. If downgrade cannot preserve new
rows safely, the migration must document that limitation and require a database backup before
upgrade.

## Non-Goals

This contract does not approve:

- contact identity or recruiter ownership
- company merge UI
- fuzzy deduplication
- external enrichment providers
- removal of company source provenance
- M5 document packet tables
- M7 recruiter communication tables
