# ADR-0005-m3-company-identity

| Field | Value |
|-------|-------|
| **Status** | Approved |
| **Date** | 2026-06-14 |
| **Owner** | Nicolay |
| **Reviewers required** | Nicolay + Francis |
| **Review state** | Direction approved by Nicolay and Francis; implementation timing still gated |
| **Related** | `docs/decisions/ADR-0002-canonical-data-model.md`; `docs/decisions/ADR-0005-final-review.md`; `docs/architecture/database-implementation-roadmap.md`; `docs/architecture/current-data-model.md`; `docs/contracts/database-schema-contract.md` |

## Review State

Nicolay and Francis have approved the proposed M3 company identity direction. This approval is
direction-only and does not authorize implementation yet.

The final review package is recorded in `docs/decisions/ADR-0005-final-review.md`. It summarizes
the current project state, the recommended decision, remaining MVP work, and the sign-off options
for Nicolay and Francis.

Do not implement the migration yet unless the implementation PR is limited to deterministic company
identity, preserves `jobs.company`, avoids source-url domain assumptions, includes placeholder
handling, and proves PostgreSQL migration plus API/dashboard compatibility.

Before the migration is implemented, the team must review the ADR and migration contract again in the
context of the active milestone and explicitly decide whether the timing is right.

## Context

M1 stores company information as a nullable `jobs.company` string. That is enough for manual intake,
dashboard display, scoring context, and the current demo path.

M3 needs first-class company identity so ApplyPilot can group jobs by employer, deduplicate repeated
intake, support recruiter/contact ownership later, and keep provenance for the raw company text found
on a job posting.

This ADR proposes the company identity contract required before any M3 migration adds a `companies`
table or `jobs.company_id`.

## Decision

Adopt a first-class `companies` table in M3 while preserving the existing `jobs.company` string as
source/provenance text during the compatibility period.

Proposed M3 company fields:

```text
id uuid PK
name varchar(256) not null
normalized_name varchar(256) not null
domain varchar(256) nullable
normalized_domain varchar(256) nullable
created_at timestamptz not null
updated_at timestamptz not null
```

Proposed `jobs` addition:

```text
company_id uuid FK -> companies.id nullable during backfill, then non-null after validation if approved
```

Identity rules:

- `normalized_domain` is the strongest deduplication key when present.
- Domain normalization lowercases the host, removes URL schemes, removes paths/query strings, strips
  a leading `www.`, and stores only the registrable company domain when it can be determined safely.
- Do not infer employer identity from a job posting `source_url`. The source URL may identify an ATS,
  job board, or redirect host rather than the employer. Use source URLs for ATS/source context only
  unless a future approved contract adds an explicit employer-domain field.
- A partial unique index should enforce uniqueness of `normalized_domain` when it is not null.
- `normalized_name` lowercases, trims whitespace, collapses internal whitespace, and strips common
  legal suffixes only when doing so is deterministic.
- Name-only deduplication is exact on `normalized_name`; no fuzzy matching in the migration.
- Unknown or blank company values map to a deterministic `Unknown Company` row.
- Confidential employer values map to a deterministic `Confidential Company` row when the source text
  clearly indicates confidentiality.
- Duplicate company merges are not automatic in M3 unless they share the same non-null
  `normalized_domain`.

Compatibility rules:

- Existing API/dashboard consumers may continue reading `jobs.company` as the display company text
  during the transition.
- `jobs.company` must not be dropped in the same migration that adds `companies`.
- Backfill should preserve the original source string in `jobs.company` even when `company_id` points
  to a normalized company row.
- Any later removal or rename of `jobs.company` requires a separate compatibility contract.

## Implementation Target

The future M3 implementation PR should:

1. Add the `companies` table.
2. Insert deterministic `Unknown Company` and `Confidential Company` rows.
3. Add nullable `jobs.company_id`.
4. Normalize existing `jobs.company` values.
5. Create company rows using deterministic domain and exact-name rules.
6. Backfill `jobs.company_id`.
7. Add indexes and constraints, including partial uniqueness for non-null `normalized_domain`.
8. Validate every job has a company mapping.
9. Make `jobs.company_id` non-null only if approved after validation.
10. Preserve API/dashboard compatibility for existing `company` display fields.

This ADR does not authorize adding contacts, recruiter threads, document packets, answer libraries,
or executor retry fields.

## Implementation Entry Conditions

Do not open an implementation PR for this migration until the team confirms timing and Francis
feedback is reviewed.

When implementation is approved, the PR must stay inside these limits:

- deterministic company identity only;
- preserve `jobs.company` as source/provenance and dashboard/API display compatibility;
- no source-url domain assumptions for employer identity;
- explicit placeholder handling for unknown and confidential company values;
- PostgreSQL migration and backfill validation;
- API and dashboard compatibility proof.

## Validation Required

The implementation PR must prove:

- `python -m alembic upgrade head` succeeds on a fresh PostgreSQL database.
- Existing M1 job/application/demo data survives migration.
- Legacy jobs with blank company text map to `Unknown Company`.
- Confidential employer text maps to `Confidential Company`.
- Jobs with the same normalized non-null domain map to the same company.
- Jobs without domains deduplicate only by exact `normalized_name`.
- API/dashboard responses remain compatible for current `company` display fields.
- `python -m pytest` passes.
- The PostgreSQL-backed seed-to-dashboard validation passes.

When local PostgreSQL is unavailable, use Remote Validation Assist for migration and backfill
validation.

## Approval Checklist

Before implementing this ADR, Nicolay and Francis should confirm:

- `companies` should be introduced in M3 before document packet or recruiter-thread normalization.
- `jobs.company` remains as source/provenance text during the compatibility period.
- Domain-based deduplication is acceptable only when `normalized_domain` is non-null.
- Name-only deduplication is exact on `normalized_name`; fuzzy matching stays out of the migration.
- `Unknown Company` and `Confidential Company` are acceptable deterministic fallback rows.
- `jobs.company_id` starts nullable for backfill and becomes non-null only after validation and
  human approval.
- The implementation PR must include PostgreSQL-backed migration, backfill, API/dashboard
  compatibility, and seed-to-dashboard validation.

## Consequences

Positive:

- M3 gets a clear, reviewable path to real company identity.
- Later contacts and recruiter-thread work can attach to companies instead of loose strings.
- Raw company text remains available for provenance and compatibility.
- The migration avoids risky fuzzy matching and hidden data merges.

Costs:

- Some duplicate companies may remain until a deliberate merge workflow exists.
- Domain normalization must be conservative to avoid false ownership.
- The model temporarily carries both `jobs.company` and `jobs.company_id`.

Not decided here:

- Contact identity and company employment history.
- Company merge UI or admin workflow.
- External enrichment providers.
- Removing or renaming `jobs.company`.
- Multi-tenant company privacy boundaries.

## Supersedes

None.

## Superseded by

None.
