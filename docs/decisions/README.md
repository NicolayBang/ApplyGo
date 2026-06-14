# Architecture Decision Records (ADRs)

Approved ADRs can supersede lower-priority documentation while remaining below the architecture PDF in authority.

## File Naming
Use: `ADR-0001-short-title.md`

## Required Sections
- Status
- Context
- Decision
- Consequences
- Supersedes (optional)
- Superseded by (optional)

## Template
```md
# ADR-0001-short-title

## Status
Proposed | Approved | Deprecated | Superseded

## Context
Why this decision is needed.

## Decision
What is decided.

## Consequences
Trade-offs, impacts, and constraints.

## Supersedes
List previous ADRs or docs if applicable.

## Superseded by
Link newer ADR if this one is replaced.
```

## Authority Reminder
Authority order:
1. `docs/architecture/OpenClaw_Final_Agreed_Architecture.pdf`
2. Approved ADRs
3. `docs/architecture/`
4. `docs/contracts/`
5. `AGENTS.md`
6. Chat discussion

## ADR Index
- `ADR-0001-architecture-operating-structure.md` (Approved)
- `ADR-0002-canonical-data-model.md` (Proposed)
- `ADR-0003-m1-database-value-checks.md` (Approved)
- `ADR-0004-m1-audit-retention.md` (Approved)
- `ADR-0005-m3-company-identity.md` (Proposed)

## Review Briefs
- `m3-company-identity-decision-brief.md` (Review brief)
- `ADR-0005-final-review.md` (Final review package)
