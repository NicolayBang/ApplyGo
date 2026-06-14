# M3 Company Identity Decision Brief

**Status:** Review brief; Nicolay approved M3 direction pending Francis review
**Decision needed:** Francis feedback and later implementation-timing confirmation.
**Decision owners:** Nicolay + Francis
**Related:** `ADR-0005-m3-company-identity.md`; `docs/contracts/m3-company-migration-contract.md`; `docs/architecture/database-implementation-roadmap.md`; `docs/architecture/current-data-model.md`

## Plain-English Decision

Should ApplyPilot introduce first-class company records in M3 while preserving the current
`jobs.company` text field during migration?

This would move the project from "company as loose text on a job" toward "company as a reusable
identity that jobs can reference." It does not approve implementing recruiter contacts, company
merge tools, external enrichment, or removing the existing company text field.

Nicolay approved this M3 direction. Francis review is still pending, and the team should review the
timing again before opening an implementation PR for the migration.

Do not implement yet unless the implementation PR is limited to deterministic company identity,
preserves `jobs.company`, avoids source-url domain assumptions, includes placeholder handling, and
proves PostgreSQL migration plus API/dashboard compatibility.

## Current State

M1 stores employer information as `jobs.company` text. That is enough for the current manual intake,
dashboard display, scoring context, policy flow, dry-run planning, and demo path.

The limitation is that plain text does not give ApplyPilot a stable company identity. The same
employer can appear under slightly different names, contacts cannot attach cleanly to an employer,
and future reporting or recruiter ownership would have to work around duplicate strings.

## Proposed Direction

M3 would add a `companies` table and add `jobs.company_id` to `jobs`.

During the compatibility period, `jobs.company` stays in place as the original source/provenance text
and as a stable display value for existing API and dashboard behavior.

The conservative identity rules are:

- use normalized domain as the strongest deduplication key when present
- use exact normalized name matching only when no domain is available
- map blank company values to `Unknown Company`
- map clearly confidential employer values to `Confidential Company`
- do not infer employer identity from job posting source URLs
- avoid fuzzy matching, AI matching, and external enrichment during migration

## Why This Helps

- Groups jobs by employer instead of isolated text strings.
- Prepares the model for contacts, recruiter ownership, and company-level history later.
- Keeps the current dashboard and API stable while the schema evolves.
- Preserves original intake text for auditability and provenance.
- Avoids risky automatic merges by keeping deduplication deterministic.

## Migration Shape

The implementation would use an add, backfill, validate, then constrain sequence:

1. Add `companies`.
2. Seed deterministic fallback rows for unknown and confidential employers.
3. Add nullable `jobs.company_id`.
4. Backfill company references from existing `jobs.company` values.
5. Add indexes and uniqueness constraints after backfill succeeds.
6. Validate every job has a company mapping.
7. Make `jobs.company_id` non-null only after validation and explicit approval.
8. Keep API/dashboard company display behavior compatible.

## Key Tradeoffs

Positive:

- Creates a cleaner foundation for the next data-model layer.
- Reduces future drift between jobs, contacts, and company-level reporting.
- Keeps migration behavior reviewable and testable.

Costs:

- Adds schema complexity before contacts are implemented.
- Some duplicates may remain when there is no reliable domain.
- The system temporarily carries both `jobs.company` and `jobs.company_id`.

## Required Validation

Before implementation is accepted, the PR should prove:

- fresh PostgreSQL Alembic upgrade succeeds
- existing M1 data survives migration
- blank and confidential company cases backfill deterministically
- domain-based deduplication works when normalized domain is present
- no-domain companies deduplicate only by exact normalized name
- API and dashboard company display behavior remains compatible
- backend pytest passes
- seed-to-dashboard PostgreSQL validation passes

## Non-Goals

This decision does not approve:

- contacts or recruiter-thread normalization
- document packet tables
- fuzzy company merging
- AI or external enrichment for companies
- removal or rename of `jobs.company`
- production data migration without explicit approval

## Review Questions

- Is M3 the right time to introduce first-class companies?
- Are the fallback rows `Unknown Company` and `Confidential Company` acceptable?
- Is exact-name fallback conservative enough for this phase?
- Should `jobs.company` remain as provenance text beyond M3?
- What validation evidence is required before making `jobs.company_id` non-null?

## Sign-Off Options

- **Approve direction:** M3 can proceed to an implementation PR following the ADR and contract.
- **Request changes:** Update the ADR, migration contract, or validation requirements before approval.
- **Defer M3:** Keep `jobs.company` as text until a later milestone.
