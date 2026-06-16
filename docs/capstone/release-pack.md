# Capstone Release Pack

**Status:** Public reviewer path  
**Audience:** recruiters, instructors, capstone reviewers, and technical readers  
**Purpose:** give a fast reading order for the current public repository

ApplyGo is best reviewed as an implemented capstone baseline, not as a finished product. The
documents below are ordered to show what exists today, how to run it, and where the current
boundaries are.

## Fast Paths

### If you have 5 minutes

1. Read `reviewer-brief.md`.
2. Skim `mvp-status.md`.
3. Look at the dashboard screenshot in the root `README.md`.

### If you have 15 minutes

1. Read `reviewer-brief.md`.
2. Read `m1-release-notes.md`.
3. Read `mvp-status.md`.
4. Open `dashboard-demo-flow.md`.

### If you want to run the demo

1. Start with `codespaces-demo.md` for the fastest setup path.
2. Use `m1-demo-script.md` if you want a guided walkthrough.
3. Use `m1-demo-review-checklist.md` or `final-manual-validation-checklist.md` to record the result.

## What To Read First

- `reviewer-brief.md`: shortest explanation of what ApplyGo is and what was built
- `mvp-status.md`: current implemented scope, non-goals, and next direction
- `m1-release-notes.md`: milestone framing, validation evidence, and handoff language
- `dashboard-demo-flow.md`: detailed runbook for the implemented dashboard workflow
- `m1-local-mvp-validation-2026-06-15.md`: concrete validation evidence from the local packaged run

## What This Repo Demonstrates

- governed workflow design
- database-backed application state and auditability
- policy-before-executor discipline
- dry-run-first automation design
- human review before external side effects
- CI, migrations, and reproducible local/Codespaces validation

## What It Does Not Claim Yet

- real job submission
- Gmail or browser automation
- LLM drafting in production flow
- production deployment
- finished end-user product polish

## Suggested Public Reading Order

1. `README.md`
2. `docs/capstone/reviewer-brief.md`
3. `docs/capstone/mvp-status.md`
4. `docs/capstone/m1-release-notes.md`
5. `docs/capstone/codespaces-demo.md` or `docs/capstone/dashboard-demo-flow.md`

## Notes For Reviewers

Future milestone material exists in the repository, but the public capstone story should stay
anchored to implemented behavior. When in doubt, prefer `README.md`, `reviewer-brief.md`,
`mvp-status.md`, and the M1 validation docs over future-looking architecture notes.
