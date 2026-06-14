# ADR-0005-m3-company-identity

| Field | Value |
|-------|-------|
| **Status** | Approved direction; proposed 3NF amendment pending review |
| **Date** | 2026-06-14 |
| **Owner** | Nicolay |
| **Reviewers required** | Nicolay + Francis |
| **Review state** | Existing direction approved; proposed 3NF completion requirements require Nicolay and Francis approval; implementation timing still gated |
| **Related** | `docs/decisions/ADR-0002-canonical-data-model.md`; `docs/decisions/ADR-0005-final-review.md`; `docs/architecture/database-implementation-roadmap.md`; `docs/architecture/current-data-model.md`; `docs/contracts/database-schema-contract.md` |

## Review State

Nicolay and Francis have approved the proposed M3 company identity direction. This approval is
direction-only and does not authorize implementation yet.

This revision proposes a stronger M3 completion boundary: company identity must finish in practical
third normal form (3NF), with one authoritative company record and no company-owned facts duplicated
on `jobs`. Nicolay and Francis must approve this amendment before it becomes binding.

The final review package is recorded in `docs/decisions/ADR-0005-final-review.md`. It summarizes
the current project state, the recommended decision, remaining MVP work, and the sign-off options
for Nicolay and Francis.

Do not implement the migration yet. If this amendment is approved, the implementation must be
limited to deterministic company identity, preserve legacy source text during migration, avoid
source-url domain assumptions, include placeholder handling, prove PostgreSQL migration plus
API/dashboard compatibility, and complete the 3NF ownership cutover defined below.

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

Adopt a first-class `companies` table in M3 as the sole authority for canonical company identity.
Preserve the existing `jobs.company` string as source/provenance text during migration, then rename
it to `company_source_text` before M3 company normalization is considered complete.

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

Proposed M3 `jobs` shape after the compatibility cutover:

```text
company_id uuid FK -> companies.id not null
company_source_text varchar(256) nullable
```

During backfill, `company_id` is temporarily nullable and the existing column remains named
`company`. Temporary compatibility state is not the M3 target state.

## Normalization Boundary

The M3 target must satisfy a practical 3NF ownership boundary. Third normal form already includes
the requirements of first and second normal form; preserving one atomic source-text attribute does
not leave the relation "at 1NF" when that attribute has a distinct provenance meaning.

```text
companies.id -> name, normalized_name, domain, normalized_domain, created_at, updated_at
jobs.id -> company_id, company_source_text, and other job-owned attributes
jobs.company_id -> companies.id
```

- `companies` owns canonical name, domain, and normalized identity.
- `jobs` owns the relationship to a company and the raw employer text captured from that job source.
- `company_source_text` is provenance, not a fallback canonical company name.
- Company-owned attributes such as canonical name, normalized name, domain, industry, website, or
  enrichment metadata must not be duplicated onto `jobs`.
- `normalized_name` and `normalized_domain` are controlled materialized identity keys on
  `companies`; one normalization implementation must calculate them transactionally. They are the
  only documented denormalization exception and exist for deterministic matching and indexes, not
  as independent business truth.
- A partial unique index enforces non-null `normalized_domain`.
- A partial unique index enforces `normalized_name` only for rows whose `normalized_domain` is null,
  matching the approved exact-name fallback without conflating domain-backed companies.

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
  only during the transition.
- `jobs.company` must not be dropped in the same migration that adds `companies`.
- Backfill should preserve the original source string in `jobs.company` even when `company_id` points
  to a normalized company row.
- After consumer cutover, the API `company` display value must be projected from `companies.name`.
- Raw intake text must be exposed separately as `company_source_text` where needed.
- A later M3 compatibility migration must rename `jobs.company` to `jobs.company_source_text`.
- M3 company normalization is not complete until canonical reads and writes use `company_id`, the
  legacy column has provenance-only semantics, and `company_id` is non-null.

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
9. Switch canonical API/dashboard reads to `companies.name` while preserving the existing `company`
   response field.
10. Require all new job writes to resolve `company_id` in the same transaction while retaining raw
    input as source text.
11. Make `jobs.company_id` non-null after validation and human approval.
12. Rename `jobs.company` to `jobs.company_source_text` in a compatibility migration after consumers
    no longer depend on the database column name.

This ADR does not authorize adding contacts, recruiter threads, document packets, answer libraries,
or executor retry fields.

## Implementation Entry Conditions

Do not open an implementation PR for this migration until the team confirms timing and Francis
feedback is reviewed.

When implementation is approved, the PR must stay inside these limits:

- deterministic company identity only;
- preserve legacy `jobs.company` data as provenance and dashboard/API display compatibility during
  migration;
- establish `companies` as the only canonical owner of company facts;
- finish M3 with required `jobs.company_id` and provenance-only `jobs.company_source_text`;
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
- Canonical company display values are read from `companies.name` after cutover.
- New writes persist a required company relationship and never treat source text as canonical truth.
- No company-owned attribute is duplicated onto `jobs`.
- The final M3 schema exposes `company_source_text` rather than an ambiguous canonical-looking
  `jobs.company` column.
- `python -m pytest` passes.
- The PostgreSQL-backed seed-to-dashboard validation passes.

When local PostgreSQL is unavailable, use Remote Validation Assist for migration and backfill
validation.

## Approval Checklist

Before implementing this ADR, Nicolay and Francis should confirm:

- `companies` should be introduced in M3 before document packet or recruiter-thread normalization.
- `jobs.company` remains as source/provenance text during the compatibility period.
- `companies` is the sole authority for canonical company facts.
- Domain-based deduplication is acceptable only when `normalized_domain` is non-null.
- Name-only deduplication is exact on `normalized_name`; fuzzy matching stays out of the migration.
- `Unknown Company` and `Confidential Company` are acceptable deterministic fallback rows.
- `jobs.company_id` starts nullable for backfill and becomes non-null after validation and human
  approval; non-null is required for M3 completion.
- `jobs.company` is renamed to `jobs.company_source_text` after API/dashboard cutover.
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
- The model temporarily carries both `jobs.company` and `jobs.company_id`; the final M3 shape uses
  required `jobs.company_id` plus provenance-only `jobs.company_source_text`.

Not decided here:

- Contact identity and company employment history.
- Company merge UI or admin workflow.
- External enrichment providers.
- Multi-tenant company privacy boundaries.

## Supersedes

None.

## Superseded by

None.
