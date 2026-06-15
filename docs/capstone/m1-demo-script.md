# M1 Demo Script

**Status:** reviewer presentation script  
**Audience:** capstone reviewers, instructors, recruiters, and project contributors  
**Estimated time:** 8-12 minutes

Use this script when presenting the current Milestone 1 MVP. It is intentionally shorter than the
full dashboard runbook and focuses on what to show, what to say, and what the reviewer should learn
from each step.

For setup commands, use `codespaces-demo.md` or `dashboard-demo-flow.md`.

## Opening Summary

ApplyPilot is a governed job application automation platform. M1 proves the platform spine:

```text
manual intake -> classification -> scoring -> policy -> dry-run executor -> audit timeline
```

The important point is control. The system does not submit applications, send emails, or perform
browser automation in M1. It records what it would do, why it is allowed or blocked, and what audit
evidence exists.

## Demo Setup

Start from a running dashboard:

```text
http://localhost:8000/ui/
```

For Codespaces, use the forwarded port `8000` URL with `/ui/`.

Before the demo, confirm:

- `/health` returns `{"status":"ok","service":"applypilot"}`;
- migrations have been applied;
- the dashboard is open;
- the current branch is `main` or the intended review branch.

## 1. Create An Application

Show the manual intake area.

Say:

> This is the human-controlled entry point. M1 starts from manual job intake so the workflow is
> deterministic and easy to audit before adding external integrations.

Click `Sample job`, then `Create`.

Point out:

- the generated application ID;
- the application summary;
- parsed job details such as role, company, location, remote status, source, job type, and salary;
- the first audit event, `application.created`.

Reviewer takeaway:

- the dashboard is connected to the backend;
- the backend persists the application in PostgreSQL;
- creation is auditable.

## 2. Show Governed Workflow State

Move the application through:

```text
ApplicationCreated -> Draft -> ReadyForReview -> Approved
```

Say:

> The state machine controls progression. The dashboard only exposes valid next transitions, and
> each state change is recorded as an audit event.

Point out:

- the progress stepper;
- current state in the application summary;
- `application.state_changed` events in the timeline;
- unavailable transitions are not shown.

Reviewer takeaway:

- workflow state is explicit;
- invalid paths are blocked by backend rules;
- the UI is guided by implemented state, not hardcoded presentation claims.

## 3. Score The Application

Click `Score application`.

Say:

> M1 uses deterministic scoring so validation is repeatable. Later LLM support can assist with
> extraction or drafting, but the current demo does not depend on an external model.

Point out:

- fit score;
- confidence;
- recommendation;
- reasons, risks, missing data, and red flags;
- `application.scored` in the timeline.

Reviewer takeaway:

- the system produces review evidence;
- scoring is inspectable and recorded;
- low-confidence or incomplete inputs can affect later policy decisions.

## 4. Evaluate Policy

Click `Evaluate policy`.

Say:

> Policy owns permission. Executor actions are not supposed to happen until a policy decision has
> been recorded.

Point out:

- the latest policy decision;
- reasons and required overrides if present;
- `policy_decision_logged` in the timeline;
- review readiness updating after policy evaluation.

Reviewer takeaway:

- permission is explicit;
- policy decisions are persisted before executor planning;
- human oversight remains visible.

## 5. Preview The Action

Click `Preview action`.

Say:

> This is the dry-run executor. It records the planned action and safeguards, but it does not send
> email, open a browser, or submit anything externally.

Point out:

- execution mode is `dry_run`;
- executor status is planned;
- `side_effects: false`;
- planned steps and required safeguards;
- `executor_attempt_logged` and `executor_result_logged` in the timeline.

Reviewer takeaway:

- external-action-like behavior is side-effect free in M1;
- executor evidence is auditable;
- the platform is built for governed automation, not uncontrolled autonomous action.

## 6. Close With Review Readiness

Show the review readiness and audit timeline sections.

Say:

> This is the reviewer view. It answers whether the application has enough recorded evidence for
> policy, preview, and eventual submission.

Point out:

- policy readiness;
- preview readiness;
- submission guardrails;
- the complete timeline from intake through executor result.

Reviewer takeaway:

- the dashboard can explain the workflow without database inspection;
- `Submitted` remains guarded behind required evidence;
- the MVP proves the core architecture before adding external integrations.

## Expected Pass Result

The demo is successful when:

- the application can be created from the sample job;
- valid workflow transitions are shown and recorded;
- scoring produces visible review evidence;
- policy is recorded before preview;
- preview remains dry-run only;
- the audit timeline shows creation, state changes, scoring, policy, executor attempt, and executor
  result;
- no part of the demo implies real application submission, Gmail automation, or browser automation.

## Known M1 Boundaries

These are intentional non-goals for this milestone:

- real application submission;
- Gmail automation;
- browser automation;
- LLM extraction or drafting;
- multi-user authentication;
- production hosting.

## If The Demo Blocks

If `Preview action` is blocked, check the policy decision and confidence level. Sparse or incomplete
input can correctly require human review. Use the built-in `Sample job` path for the intended M1
happy-path demo.

If the dashboard cannot create or load an application, pause the demo and run the validation steps in
`m1-demo-review-checklist.md`.
