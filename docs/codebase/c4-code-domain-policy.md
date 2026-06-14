# C4 Code Level: Policy Domain

## Overview

- **Location**: `backend/src/applypilot/domain/policy/`
- **Purpose**: Produce deterministic, auditable permission decisions before executor work.
- **Outputs**: `ALLOW`, `DENY`, or `REVIEW`, with reasons and required overrides.

## Domain Models

### Enums

| Enum | Values |
|---|---|
| `AutomationMode` | `manual`, `semi_auto`, `full_auto`, `dry_run` |
| `ConfidenceLevel` | `high`, `medium`, `low` |
| `PolicyDecisionOutcome` | `allow`, `deny`, `review` |
| `WorkerType` | `email`, `browser`, `documents` |

### `PolicyContext`

Carries scoring and risk evidence:

- `confidence`
- optional `fit_score`
- optional `recommendation`
- `reasons`
- `risks`
- `missing_data`
- `red_flags`

### `PolicyRequest`

Identifies the application, current state, requested action, worker, context, and
automation mode presented to the policy gate.

### `PolicyDecision`

Contains `decision`, `mode`, `reasons`, `required_overrides`, a generated decision UUID,
and creation time. Its `allowed` property is true only for `ALLOW`.

## `PolicyEngine`

`PolicyEngine.evaluate()` short-circuits on the first matching rule:

| Priority | Condition | Outcome |
|---|---|---|
| 1 | Low confidence | `REVIEW` with `human_review` |
| 2 | Red flags in full-auto | `DENY` with `manual_override` |
| 2 | Red flags in another mode | `REVIEW` with `human_review` |
| 3 | Not recommended in full-auto | `DENY` with `manual_override` |
| 3 | Not recommended in another mode | `REVIEW` with `human_review` |
| 4 | Fit score below 45 | `REVIEW` with `score_review` |
| 5 | Manual mode | `REVIEW` with `human_approval` |
| 6 | Missing data | `REVIEW` with `complete_missing_data` |
| 7 | Risks outside dry-run | `REVIEW` with `risk_review` |
| 8 | Dry-run after prior checks | `ALLOW`, explicitly without side effects |
| Default | All checks passed | `ALLOW` |

Dry-run is therefore not an unconditional bypass: confidence, red flags, recommendation,
low score, and missing-data checks still run first.

## API Schemas

`PolicyContextInput` validates optional score context. `PolicyEvaluationRequest` supplies
the requested action, worker, optional context, optional mode, and actor.
`PolicyDecisionRead` exposes the persisted decision, permission boolean, reasons, risks,
overrides, and timestamp.

## Persistence and Audit

The API builds a context from an explicit request or the stored application score.
`Tracker.record_policy_decision()` writes the decision before execution and appends a
`policy_decision_logged` event containing the decision evidence.

## Tests

`backend/tests/unit/test_policy_engine.py` covers all major decision branches. Integration
tests verify persistence, score-derived context, audit logging, and not-recommended review.
