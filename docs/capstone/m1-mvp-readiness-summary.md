# M1 MVP Readiness Summary

**Status:** Near MVP; final manual demo pass still recommended  
**Date:** 2026-06-14  
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

## Remaining Before Calling M1 Complete

- Run one final manual demo pass on current `main`.
- Confirm the dashboard path works end to end:

```text
Sample job -> Create -> Score -> state progression -> Policy -> Dry-run -> audit timeline
```

- Confirm the UI still communicates governed behavior clearly:
  - no real submission;
  - no Gmail or browser automation;
  - dry-run only;
  - policy and executor evidence required before submission-like state changes.
- Record any final pass/fix notes in `docs/capstone/m1-demo-review-checklist.md` or a dated
  validation note.

## Explicitly Out Of MVP Scope

- Real external job submission.
- Gmail automation.
- Browser automation.
- LLM drafting or extraction.
- Multi-user authentication.
- Production deployment.
- M3 company identity migration, unless the team explicitly reopens timing and validation review.

## Current Assessment

M1 is functionally close to MVP. The remaining work is mostly demo confidence, visual polish, and
final validation rather than core backend architecture.

Recommended next action:

1. Complete the final manual demo pass against current `main`.
2. Accept or update the dashboard workflow validation PR from the manual result.
3. Record the final pass/fix outcome in the capstone validation docs.
4. If the pass is clean, mark M1 MVP complete for capstone review.
