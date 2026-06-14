# M1 Manual Demo Validation - 2026-06-14

**Status:** Passed with one governed demo-path follow-up fixed afterward  
**Environment:** GitHub Codespaces, port `8000` forwarded  
**Branch tested:** `main`  
**Backend:** FastAPI + PostgreSQL with migrations `0001` through `0007` applied

This note records the manual M1 dashboard validation run used to confirm the reviewer-facing MVP
path. It is evidence for the current capstone demo, not a new scope or architecture authority
document.

## Environment Checks

| Check | Result |
| --- | --- |
| Docker Compose PostgreSQL and Redis started | Pass |
| Migrations applied | Pass |
| `python -m pytest` | Pass, 87 tests |
| `python -m scripts.validate_seed_to_dashboard` | Pass |
| Backend server started | Pass |
| `GET /health` | Pass |
| `GET /ui/` | Pass |

## Dashboard Workflow Checks

| Area | Result |
| --- | --- |
| Sample job prefill and create | Pass |
| Application ID and summary display | Pass |
| Initial state `ApplicationCreated` | Pass |
| State progression through `Draft`, `ReadyForReview`, and `Approved` | Pass |
| Invalid state transitions hidden | Pass |
| Scoring result displayed | Pass |
| Reasons, risks, missing data, and red flags displayed | Pass |
| Policy decision recorded and shown | Pass |
| Audit timeline records creation, state changes, scoring, and policy | Pass |

## Governance Observation

During the first live UI pass, dry-run was correctly blocked by policy because the sample job path
did not provide enough data to reach high confidence. The policy engine required human review rather
than allowing executor planning.

This was correct governed behavior, not a policy bug.

Follow-up PR `fix(dashboard): unblock governed demo dry-run path` updated the built-in dashboard
sample so deterministic intake classification can infer ATS, job type, salary, and enough job detail
for the approved M1 happy path. It also kept the blocked-policy path intact and improved dashboard
feedback when policy requires review.

## API-Level Dry-Run Evidence

The full dry-run contract was validated with an enriched job record:

- executor status `planned`;
- execution mode `dry_run`;
- `side_effects=false`;
- planned steps and requirements populated;
- `executor_attempt_logged` and `executor_result_logged` visible in the audit timeline.

## Result

The M1 demo is MVP-presentable after the dashboard sample-data follow-up, assuming CI remains green
and the reviewer follows `docs/capstone/dashboard-demo-flow.md`.
