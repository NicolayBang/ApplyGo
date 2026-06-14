# C4 Code Level: Frontend Dashboard

## Overview

- **Location**: `frontend/`
- **Implementation**: Dependency-free HTML, CSS, and JavaScript.
- **Serving modes**: Static-file preview or FastAPI `/ui`.
- **Purpose**: Demonstrate and inspect the governed Milestone 1 workflow.

## Files

| File | Responsibility |
|---|---|
| `index.html` | Dashboard structure and workflow controls |
| `styles.css` | Visual system and responsive layout |
| `app.js` | Demo fixture, API client, rendering, workflow actions |
| `README.md` | Runbook and troubleshooting |

## `app.js` Responsibilities

### State and fixtures

- `demoAudit` supports offline review.
- `demoReviewSummary` supports offline review-readiness rendering.
- `stateTransitions` mirrors the backend transition graph for available controls.
- `sampleJob` prefills a repeatable manual-intake demonstration.
- `visibleStateTransitions()` hides submission until audit prerequisites are present.

### Rendering

- `renderSummary()` displays job, workflow, and score context.
- `renderStateActions()` exposes only valid next-state controls.
- `renderScoreDetails()` displays score evidence and review signals.
- `renderPolicy()` shows outcome explanations and required overrides.
- `renderExecutor()` shows side-effect status, safeguards, and planned steps.
- `renderReviewSummary()` shows policy, dry-run, submission, and next-state readiness.
- `eventSummary()` and `renderTimeline()` produce readable audit-event descriptions.
- `renderAudit()` coordinates the complete response.

### API and workflow actions

- `createManualApplication()` creates a job and application.
- `scoreApplication()` records deterministic scoring.
- `transitionApplicationState()` applies a selected valid transition.
- `evaluatePolicy()` records a policy decision.
- `dryRunFollowUp()` submits a policy-authorized dry-run plan.
- `loadAudit()` refreshes the full audit summary and compact review summary.

### Safety and readiness

The dashboard validates UUIDs, tracks whether an application is loaded, disables actions
whose prerequisites are missing, and requires an allowed recorded policy decision before
offering the dry-run action. It also requires matching policy and executor evidence before
offering the `Submitted` state transition. The review-readiness panel surfaces the same evidence in
a compact reviewer view.

## Validation

CI runs `node --check frontend/app.js` as a lightweight syntax gate for the dependency-free
dashboard. Backend integration tests continue to verify that the dashboard assets are
served, expose the expected workflow controls, and keep JavaScript selectors aligned with the HTML
asset contract.

## API Contract

The dashboard uses the same-origin API by default, with configurable local API-base support
for static-file preview. Its primary read model is:

- `GET /applications/{application_id}/audit`
- `GET /applications/{application_id}/review-summary`

The audit response contains the application, ordered events, policy decisions, and executor actions.
The review-summary response contains compact readiness flags and guarded next states.

## Scope

The dashboard does not perform browser automation, send email, generate documents, or
submit live applications.
