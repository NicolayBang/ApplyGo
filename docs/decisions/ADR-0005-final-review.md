# ADR-0005 Final Review: M3 Company Identity

**Status:** Direction approved; implementation timing still gated

**Date:** 2026-06-14

**Decision owners:** Nicolay + Francis

**Sign-off:** Nicolay approved; Francis approved

**Related:** `ADR-0005-m3-company-identity.md`; `m3-company-identity-decision-brief.md`; `docs/contracts/m3-company-migration-contract.md`; `docs/capstone/mvp-status.md`

## Recommended Decision

ADR-0005 direction is approved for M3, but the migration must not be implemented yet.

The decision should authorize the design direction only:

- introduce first-class company identity in M3;
- preserve `jobs.company` as source/provenance text during the compatibility period;
- avoid employer-domain assumptions from job posting `source_url`;
- use deterministic placeholder rows for `Unknown Company` and `Confidential Company`;
- require PostgreSQL migration, API compatibility, dashboard compatibility, and seed-to-dashboard validation before merge.

Implementation remains blocked until the team explicitly confirms that M3 company identity is the
right next schema change.

## Project Summary So Far

ApplyPilot is now a governed job application automation platform spine. It is not a finished
application-submission product yet, but the core foundation is in place:

- manual job intake exists through the API and dashboard;
- job metadata is normalized and classified deterministically for the M1 demo path;
- applications are persisted in PostgreSQL with jobs, policy decisions, executor actions, and audit events;
- workflow state changes go through the application state machine;
- policy decisions are recorded before dry-run executor actions;
- dry-run execution records planned work without external side effects;
- audit and review summary endpoints expose the evidence needed for human review;
- the dashboard supports intake, scoring, policy, dry-run, audit, and filtered application views;
- Docker Compose, Alembic migrations, backend tests, frontend syntax checks, and CI gates are in place.

The repository currently demonstrates architecture-first implementation, migration discipline,
auditability, and human oversight before external automation.

## Why ADR-0005 Matters

The current M1 model stores employer text directly on `jobs.company`. That is appropriate for the
current demo, but it will become limiting when ApplyPilot needs employer-level history, recruiter
contacts, reporting, or duplicate job grouping.

ADR-0005 creates a controlled path from loose company text to stable company identity without
breaking the current API or dashboard. The important safety choice is to preserve the original
company text while adding normalized identity in a separate, reviewable migration.

## Review Position

The ADR was approved for direction because:

- the M1 schema is already real PostgreSQL, not throwaway mock state;
- the current dashboard and API still depend on a displayable company string;
- the proposed M3 migration has explicit compatibility and validation rules;
- risky behavior is excluded: fuzzy matching, AI matching, external enrichment, and source-url employer inference;
- the migration is gated by PostgreSQL-backed evidence rather than documentation alone.

The ADR remains unimplemented until the team confirms timing. If M1 MVP work needs more
dashboard polish or workflow completion first, ADR-0005 can stay approved in direction while the
migration waits.

## What Is Left For MVP

The remaining MVP work is mostly product completion around the already-built spine:

- tighten the dashboard review flow around application summaries, audit evidence, and next actions;
- keep seed-to-dashboard validation easy to run in Codespaces/PostgreSQL;
- add any missing frontend smoke coverage once the UI stabilizes;
- improve reviewer-facing README/demo instructions;
- decide whether M3 company identity should land before or after the first polished MVP demo;
- keep real Gmail, browser automation, LLM drafting, multi-user auth, and production deployment out of MVP scope unless explicitly re-scoped.

The MVP should continue to prove controlled automation, not broad autonomous submission.

## Final Review Questions

Nicolay and Francis should confirm:

- Is M3 the right milestone to introduce first-class companies?
- Should `jobs.company` remain as source/provenance text during the compatibility period?
- Are `Unknown Company` and `Confidential Company` acceptable deterministic fallback rows?
- Is exact normalized-name matching acceptable when no safe domain is present?
- Should the implementation PR make `jobs.company_id` non-null immediately, or only after a validation PR proves the backfill?
- Is the required validation list strong enough for a schema migration that affects API and dashboard compatibility?

## Sign-Off Record

**Approved direction:** Nicolay and Francis approved ADR-0005 as the M3 company identity direction.
Implementation still waits for explicit timing approval.

**Implementation gate:** Before opening a migration PR, the team must confirm timing and preserve the
implementation limits from ADR-0005 and the M3 company migration contract.

**Allowed future change:** If timing or validation concerns change, update the ADR or migration
contract before implementation starts.

## Non-Goals For This Decision

This final review does not approve:

- implementing the migration in this PR;
- removing or renaming `jobs.company`;
- fuzzy company merging;
- AI or external enrichment for company identity;
- contacts, recruiter threads, document packets, answer libraries, or executor retry schema changes;
- real external submission automation.
