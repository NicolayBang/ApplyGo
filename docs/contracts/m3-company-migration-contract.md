# M3 Company Migration Contract

**Status:** Direction approved; implementation timing still gated

**Scope:** Future M3 migration from `jobs.company` text to first-class company identity

**Authority:** Approved M3 direction contract; does not authorize migration until timing is approved

**Review state:** Nicolay and Francis approved M3 direction; later implementation timing review
required

**Related:** `docs/decisions/ADR-0005-m3-company-identity.md`,
`docs/contracts/database-schema-contract.md`, `docs/architecture/database-implementation-roadmap.md`

This contract defines the safety boundary for the future M3 company identity migration. It is not an
implemented schema description. The current M1 source of truth remains `jobs.company` until an
approved migration changes the database, ORM, API, dashboard, tests, and documentation together.

Nicolay and Francis approved this direction for M3, but implementation remains gated. Before any
schema migration starts, the team should explicitly confirm that the current milestone is ready for
company identity work.

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

The migration must preserve `jobs.company` as source/provenance text until a later approved
compatibility contract removes or renames it.

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
7. Make `jobs.company_id` non-null only after validation and human approval.
8. Keep the existing `jobs.company` field available to API/dashboard consumers.

## API And Dashboard Compatibility

During the compatibility period:

- API responses must continue exposing a display company string for existing consumers.
- Dashboard rows must keep showing company text without requiring frontend rewrites in the same PR.
- New API fields for normalized company identity should be additive.
- Write behavior must define whether incoming company text creates, reuses, or references a company.
- Any deprecation or removal of `jobs.company` requires a later PR and explicit approval.

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
- full backend pytest suite
- seed-to-dashboard validation against PostgreSQL

When local PostgreSQL is unavailable, request Remote Validation Assist and record the result in the
PR.

## Implementation Entry Conditions

An implementation PR is allowed only after the team explicitly confirms timing. That PR must remain
limited to:

- deterministic company identity migration;
- preserving `jobs.company`;
- explicit `Unknown Company` and `Confidential Company` placeholder handling;
- no source-url domain assumptions;
- PostgreSQL migration, backfill, and constraint validation;
- API and dashboard compatibility for existing company display behavior.

## Approval Checklist

Before this contract is implemented, Nicolay and Francis should confirm:

- Backfill may create `Unknown Company` and `Confidential Company` rows.
- The migration preserves original `jobs.company` text.
- No fuzzy matching, AI matching, or external enrichment runs during backfill.
- API and dashboard compatibility for the existing company display field is required in the same
  implementation PR.
- Making `jobs.company_id` non-null requires validation evidence and explicit human approval.
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
- removal of `jobs.company`
- M5 document packet tables
- M7 recruiter communication tables
