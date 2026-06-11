# Policy Contract

## Purpose
Define how policy evaluates action requests across automation modes.

## Modes
- `manual`
- `semi_auto`
- `full_auto`
- `dry_run`

## Input Schema
```json
{
  "application_id": "uuid",
  "current_state": "string",
  "requested_action": "string",
  "worker": "email|browser|documents",
  "context": {
    "confidence": "high|medium|low",
    "reasons": [],
    "risks": [],
    "missing_data": [],
    "red_flags": []
  },
  "mode": "manual|semi_auto|full_auto|dry_run"
}
```

## Output Schema
```json
{
  "decision_id": "uuid",
  "decision": "allow|deny|review",
  "mode": "manual|semi_auto|full_auto|dry_run",
  "reasons": [],
  "required_overrides": [],
  "created_at": "ISO-8601"
}
```

## Required Behaviors
- Low-confidence outcomes force review.
- Denied actions map to `blocked_by_policy` unless overridden by approved process.
- `dry_run` mode allows planning path only and disallows side effects.
- Log all policy decisions before executor invocation.

## Milestone Note
Policy engine behavior is documented first; code implementation remains minimal/stub.