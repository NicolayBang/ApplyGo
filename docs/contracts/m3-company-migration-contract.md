# M3 Company Migration Contract

**Status:** Implemented M3 baseline

**Scope:** Completed M3 migration from `jobs.company` text to first-class company identity

**Authority:** Implemented M3 company identity baseline contract

**Review state:** Direction approved by Nicolay and Francis; implementation PR requires final
merge-gate review because it changes schema constraints and column names

**Related:** `docs/decisions/ADR-0005-m3-company-identity.md`,
`docs/contracts/database-schema-contract.md`, `docs/architecture/database-implementation-roadmap.md`

This contract defines the safety boundary for the implemented M3 company identity migration. The
cutover is limited to deterministic company identity, avoids source-url domain assumptions, includes
placeholder handling, preserves raw intake provenance, and requires PostgreSQL migration plus
API/dashboard compatibility evidence.

## Starting Point

The pre-M3 schema stored company display text directly on `jobs.company`.

Current behavior that must remain compatible during the M3 transition:

- manual intake can create a job without a company
- dashboard/API consumers can read a displayable `company` value
- existing jobs and applications survive migration without data loss
- M1 audit records remain unchanged

## Implemented Shape

The implemented M3 baseline uses:

```text
companies
jobs.company_id -> companies.id
jobs.company_source_text
```

Migration `0010` preserves `jobs.company` as source/provenance text during backfill. Migration
`0011` completes the baseline by making `jobs.company_id` required and renaming the legacy column to
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

The implementation uses an add/backfill/constrain sequence:

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

After cutover:

- API responses must continue exposing a display `company` string for existing consumers, projected
  from `companies.name`.
- Dashboard rows must keep showing company text without requiring frontend rewrites in the same PR.
- An additive `company_source_text` field exposes raw intake provenance where needed.
- New writes must deterministically create or reuse a company and persist `company_id` in the same
  transaction.
- The database no longer exposes an ambiguous canonical-looking `jobs.company` column.

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

## Implementation Boundary

The implementation remains limited to:

- deterministic company identity migration;
- preserving legacy `jobs.company` values as provenance during migration;
- establishing `companies` as the only canonical owner of company facts;
- completing the cutover to required `jobs.company_id` and `jobs.company_source_text`;
- explicit `Unknown Company` and `Confidential Company` placeholder handling;
- no source-url domain assumptions;
- PostgreSQL migration, backfill, and constraint validation;
- API and dashboard compatibility for existing company display behavior.

## Approval Checklist

Before merging the cutover, Nicolay and Francis should confirm:

- Backfill may create `Unknown Company` and `Confidential Company` rows.
- The migration preserves original `jobs.company` text.
- The completed M3 schema renames that provenance field to `company_source_text`.
- No fuzzy matching, AI matching, or external enrichment runs during backfill.
- API and dashboard compatibility for the existing company display field is required in the same
  implementation PR.
- Making `jobs.company_id` non-null has validation evidence and explicit human approval.
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
