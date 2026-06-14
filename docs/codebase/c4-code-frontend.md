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
- `stateTransitions` mirrors the backend transition graph for available controls.
- `sampleJob` prefills a repeatable manual-intake demonstration.
- `visibleStateTransitions()` hides submission until audit prerequisites are present.

### Rendering

- `renderSummary()` displays job, workflow, and score context.
- `renderStateActions()` exposes only valid next-state controls.
- `renderScoreDetails()` displays score evidence and review signals.
- `renderPolicy()` shows outcome explanations and required overrides.
- `renderExecutor()` shows side-effect status, safeguards, and planned steps.
- `eventSummary()` and `renderTimeline()` produce readable audit-event descriptions.
- `renderAudit()` coordinates the complete response.

### API and workflow actions

- `createManualApplication()` creates a job and application.
- `scoreApplication()` records deterministic scoring.
- `transitionApplicationState()` applies a selected valid transition.
- `evaluatePolicy()` records a policy decision.
- `dryRunFollowUp()` submits a policy-authorized dry-run plan.
- `loadAudit()` refreshes the full audit summary.

### Safety and readiness

The dashboard validates UUIDs, tracks whether an application is loaded, disables actions
whose prerequisites are missing, and requires an allowed recorded policy decision before
offering the dry-run action. It also requires matching policy and executor evidence before
offering the `Submitted` state transition.

## API Contract

The dashboard uses the same-origin API by default, with configurable local API-base support
for static-file preview. Its primary read model is:

`GET /applications/{application_id}/audit`

The response contains the application, ordered events, policy decisions, and executor
actions.

## Scope

The dashboard does not perform browser automation, send email, generate documents, or
submit live applications.
