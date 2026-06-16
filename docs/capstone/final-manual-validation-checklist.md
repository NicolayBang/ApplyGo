# Final Manual Validation Checklist

**Status:** Ready for manual validation  
**Audience:** Nicolay, Francis, reviewers, and demo operators  
**Scope:** current MVP demo path on `main`

Use this checklist for the final human pass before presenting the current ApplyPilot MVP. It is
intended to catch demo-readiness issues that automated tests do not prove well: visual clarity,
workflow legibility, browser behavior, and whether the audit story is easy to explain.

High-risk schema or architecture PRs should be validated separately after review. Do not treat this
checklist as approval to merge database migrations, architecture authority changes, CI changes, or
external automation.

## Environment

Record the validation context:

```text
Date:
Tester:
Branch / commit:
Environment: local Docker / Codespaces
Browser:
Backend URL:
Dashboard URL:
```

## Startup

- [ ] `docker compose up -d postgres redis` starts PostgreSQL and Redis.
- [ ] `docker compose run --rm migrate` completes without migration errors.
- [ ] Backend starts with `python -m uvicorn applypilot.main:app --host 0.0.0.0 --port 8000`.
- [ ] `GET /health` returns `{"status":"ok","service":"applypilot"}`.
- [ ] `/ui/` loads the dashboard without a blank screen or console-breaking issue.

## Happy Path

- [ ] `Sample job` fills a complete reviewer-friendly opportunity.
- [ ] `Create` creates an application and displays an application ID.
- [ ] The application summary shows role, company, location, job type, source, and salary when
  available.
- [ ] Recent applications refresh and selecting the new application reloads the same record.
- [ ] State progression works through the visible allowed steps.
- [ ] Invalid or unavailable transitions are hidden or blocked.
- [ ] `Score application` records fit score, confidence, recommendation, reasons, risks, missing
  data, and red flags.
- [ ] `Evaluate policy` records a visible policy decision.
- [ ] Dry-run/preview action remains side-effect-free and clearly marked as a planned action.
- [ ] Review readiness updates after score, policy, and executor evidence.
- [ ] Audit timeline includes application creation, state changes, scoring, policy, and executor
  events in understandable order.

## Governance Story

- [ ] The UI makes it clear ApplyPilot is governed workflow automation, not an autonomous bot.
- [ ] Policy comes before executor activity.
- [ ] Dry-run evidence shows no external side effects.
- [ ] Human review remains visible before real submission behavior.
- [ ] Audit evidence is explainable to a reviewer without opening the database.

## UI Polish Pass

- [ ] Main dashboard sections are visually scannable on desktop.
- [ ] Mobile/narrow layout stacks without overlapping text or clipped controls.
- [ ] Empty/loading/error states are understandable enough for a demo.
- [ ] Buttons give clear feedback after actions.
- [ ] Copy avoids overclaiming unimplemented Gmail, browser automation, LLM, or real submission
  behavior.
- [ ] No obvious typo, stale milestone label, or misleading future-state claim appears in the demo
  surface.

## Backend Evidence

- [ ] Automated backend tests are green in CI or locally.
- [ ] Frontend quality gate is green in CI or locally.
- [ ] PostgreSQL-backed seed-to-dashboard validation passes when run in the target environment.
- [ ] Any skipped or unavailable validation is recorded with a reason.

## Result

Record the final decision:

```text
Overall result: Pass / Pass with notes / Needs fix
Blocking issues:
Non-blocking polish:
Decision:
Follow-up PRs:
```

Recommended rule: if the happy path, governance story, and automated gates pass, minor visual polish
should not block the MVP demo. If policy ordering, dry-run clarity, audit evidence, or migration
validity is unclear, fix before presenting.
