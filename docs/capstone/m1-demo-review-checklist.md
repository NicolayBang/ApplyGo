# M1 Demo Review Checklist

**Status:** Reviewer checklist

**Audience:** Nicolay, Francis, instructors, reviewers

Use this checklist when manually reviewing the M1 dashboard demo. It is a quick pass/fix aid, not a
new scope document.

## Review Record

- Date:
- Reviewer:
- Environment: local Docker / Codespaces
- Commit or PR:
- Result: pass / fix needed
- Follow-up notes:

## Setup

- [ ] PostgreSQL and Redis start with Docker Compose.
- [ ] Migrations complete successfully.
- [ ] Backend starts on port `8000`.
- [ ] `/health` returns `{"status":"ok","service":"applypilot"}`.
- [ ] Dashboard opens at `/ui/`.

## Manual Intake

- [ ] Sample job prefill works.
- [ ] Manual job creation returns a new application ID.
- [ ] Recent applications can load and select the created application.
- [ ] Application summary shows role, company, location, state, and parsed job metadata.
- [ ] Audit timeline includes `application.created`.

## Workflow

- [ ] State buttons show only valid next transitions.
- [ ] Application can move through `ApplicationCreated -> Draft -> ReadyForReview -> Approved`.
- [ ] Each transition appends `application.state_changed`.
- [ ] `Submitted` is not offered until policy and executor evidence exist.

## Scoring And Policy

- [ ] `Score application` records fit score, confidence, recommendation, reasons, and risks.
- [ ] `Evaluate policy` records a policy decision.
- [ ] Policy decision appears in both the policy panel and audit timeline.
- [ ] Review readiness marks policy/dry-run readiness appropriately.

## Dry-Run And Audit

- [ ] `Preview action` requires an allowed policy decision.
- [ ] Executor action records `execution_mode=dry_run`.
- [ ] Executor result shows `side_effects=false`.
- [ ] Planned steps and safeguards are visible.
- [ ] Audit timeline includes executor attempt and result events.
- [ ] Review readiness shows submission evidence when the dry-run exists.

## Validation

- [ ] `python -m ruff check .` passes from `backend/`.
- [ ] `python -m pytest` passes from `backend/`.
- [ ] `python -m scripts.validate_seed_to_dashboard` passes when PostgreSQL is running.
- [ ] GitHub CI is green.

## Pass Criteria

The demo is MVP-presentable when:

- the end-to-end path can be completed without editing the database manually;
- reviewers can explain what happened from the dashboard alone;
- every external-action-like step remains dry-run only;
- audit evidence is visible for creation, state, policy, executor attempt, and executor result;
- any rough edge is documented as a follow-up rather than hidden.

## Stop Conditions

Pause and fix before calling M1 MVP if:

- the dashboard cannot create or load an application;
- policy can be bypassed before dry-run;
- `Submitted` can be reached without policy plus executor evidence;
- audit evidence is missing for a material workflow step;
- the demo implies Gmail, browser automation, LLM drafting, or real submission exists.
