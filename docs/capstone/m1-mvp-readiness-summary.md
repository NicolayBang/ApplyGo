# M1 MVP Readiness Summary

**Status:** M1 MVP-presentable for capstone review
**Date:** 2026-06-15
**Audience:** Nicolay, Francis, reviewers, instructors, recruiters

ApplyPilot now has a working governed automation spine for the M1 demo. The repo demonstrates a
database-backed workflow where a job can be manually entered, classified, scored, policy-checked,
dry-run planned, and audited without performing external side effects.

This document summarizes current MVP readiness. It does not approve new scope or replace the
architecture, contracts, or ADRs.

## What Is MVP-Ready

- Manual job intake can create jobs and applications from the dashboard.
- Deterministic classification enriches supported job metadata for the demo path.
- PostgreSQL migrations define the current persisted workflow data.
- Application state transitions are guarded and audited.
- Scoring, policy decisions, and dry-run executor actions are recorded.
- Dry-run execution remains side-effect free.
- Review readiness and audit timeline make the workflow inspectable.
- CI covers backend linting, migrations, tests, app import, frontend syntax, and dashboard asset
  contracts.
- Reviewer-facing docs explain the demo flow, validation result, and current MVP boundaries.

## Final Validation Result

The final local M1 validation passed on current `main` and is recorded in
`docs/capstone/m1-local-mvp-validation-2026-06-15.md`.

Confirmed:

- Docker Compose `app` profile starts the packaged backend and dashboard.
- `GET /health` returns the expected backend health response.
- `GET /ui/` serves the dashboard from the backend container.
- The dashboard can create a job/application through the backend.
- `GET /applications` returns the created application.
- The created application's audit endpoint records `application.created` with
  `ApplicationCreated` state.

The full guided demo path remains:

```text
Sample job -> Create -> Score -> state progression -> Policy -> Dry-run -> audit timeline
```

The UI still communicates governed behavior clearly: no real submission, no Gmail or browser
automation, dry-run only, and policy/executor evidence required before submission-like state
changes.

## Explicitly Out Of MVP Scope

- Real external job submission.
- Gmail automation.
- Browser automation.
- LLM drafting or extraction.
- Multi-user authentication.
- Production deployment.
- M3 company identity migration, unless the team explicitly reopens timing and validation review.

## Current Assessment

M1 is MVP-presentable for capstone review. Remaining work should move to post-M1 planning unless a
reviewer finds a concrete defect during demo review.

Recommended next action:

1. Keep the current M1 demo stable.
2. Avoid adding new M1 scope unless a validation defect is found.
3. Review deferred M2/M3 architecture PRs after M1 closeout.
