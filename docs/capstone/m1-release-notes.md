# M1 Release Notes

**Status:** MVP-presentable release marker
**Date:** 2026-06-15
**Audience:** reviewers, instructors, recruiters, and project contributors

Milestone 1 establishes the ApplyGo platform spine. It is not a finished job application product,
but it is ready to demonstrate the governed workflow model that future automation will build on.

## Release Summary

M1 demonstrates:

- manual job intake through the dashboard;
- deterministic job classification and scoring;
- governed application state progression;
- recorded policy decisions before executor planning;
- side-effect-free dry-run executor records;
- review readiness based on score, policy, executor, and state evidence;
- audit timeline visibility from creation through preview;
- PostgreSQL-backed persistence with Alembic migrations;
- local Docker and Codespaces validation paths.

The core demo path is:

```text
manual intake -> classify -> score -> policy -> dry-run preview -> review readiness -> audit timeline
```

## Reviewer-Facing Behavior

Reviewers can create a sample application, move it through the workflow, score it, evaluate policy,
preview the governed action, and inspect the audit timeline from the dashboard.

The demo is designed to show:

- human control at the intake and approval points;
- policy before executor action;
- no real external side effects;
- inspectable scoring and policy evidence;
- clear separation between implemented M1 behavior and future automation.

## Validation Evidence

Recent M1 validation includes:

- GitHub CI frontend and backend quality gates;
- backend pytest coverage for API behavior, state guards, policy, executor, model constraints, and
  dashboard contracts;
- PostgreSQL-backed migration and seed-to-dashboard validation through Docker;
- manual frontend-backend validation recorded in capstone docs;
- reviewer runbooks for local and Codespaces demos.

Primary evidence files:

- `docs/capstone/m1-local-mvp-validation-2026-06-15.md`
- `docs/capstone/m1-manual-demo-validation-2026-06-14.md`
- `docs/capstone/m1-demo-review-checklist.md`
- `docs/capstone/dashboard-demo-flow.md`

## Known Boundaries

M1 intentionally does not include:

- real application submission;
- Gmail automation;
- browser automation;
- LLM extraction or drafting;
- multi-user authentication;
- production hosting;
- normalized future company/contact/document/thread tables.

These are future milestone concerns and should not be implied during the M1 demo.

## Handoff Notes

Recommended presentation order:

1. Start with `reviewer-brief.md`.
2. Use `codespaces-demo.md` or local Docker setup to start the app.
3. Present with `m1-demo-script.md`.
4. Validate with `m1-demo-review-checklist.md`.
5. Use `mvp-status.md` to explain current scope and boundaries.

Recommended next milestone direction:

- keep M1 stable as the capstone demo baseline;
- postpone ADR-0005 implementation until after the M1 presentation baseline is accepted;
- avoid external automation until policy, dry-run, and audit guardrails remain proven;
- improve presentation polish without overstating implemented functionality.

## Release Decision

M1 is suitable as an MVP-presentable capstone baseline when:

- GitHub CI is green;
- the dashboard demo can complete the sample path;
- dry-run remains side-effect free;
- audit evidence is visible for material workflow events;
- reviewers can understand the project from the README and capstone docs without private chat
  context.
