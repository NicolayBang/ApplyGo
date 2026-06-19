# HTTP API Contract

**Status:** implemented boundary
**Scope:** current FastAPI routes consumed by the dashboard
**Does not authorize new endpoints:** Yes

This contract records the current HTTP boundary between the FastAPI backend and the React dashboard.
It describes implemented behavior only. It does not approve future Gmail, browser automation, real
submission, authentication, or external integration endpoints.

## Contract Rules

- API responses must stay compatible with the dashboard types in `frontend/app/src/api/types.ts`.
- New external side effects still require policy, executor, audit, and human approval gates.
- State changes must pass through the state machine endpoint and record audit evidence.
- Dry-run executor calls require an allowed recorded policy decision for the same application.
- Packet review persistence records human review evidence only; it does not submit applications or
  send packet content externally.

## System Endpoint

### `GET /health`

Returns a basic service health payload:

```json
{
  "status": "ok",
  "service": "applypilot"
}
```

## Application Workflow Endpoints

### `POST /jobs`

Creates a normalized job record.

Request fields used by the dashboard:

```json
{
  "source_url": "string|null",
  "raw_text": "string|null",
  "title": "string|null",
  "company": "string|null",
  "location": "string|null",
  "remote_ok": false
}
```

Response is `JobRead`, including compatible `company` display text, optional `company_id`, and
optional `company_source_text`.

### `POST /applications`

Creates an application for an existing job.

```json
{
  "job_id": "uuid",
  "automation_mode": "manual"
}
```

Returns `ApplicationRead`. Missing jobs return `404`.

### `GET /applications`

Lists applications for the recent-applications dashboard panel.

Supported query parameters:

```text
state
recommendation
company
created_from
created_to
sort_by
sort_dir
limit
offset
```

Invalid filter or sort values return `400`.

### `PATCH /applications/{application_id}/state`

Transitions application state through the state machine.

```json
{
  "state": "ApplicationCreated|Draft|ReadyForReview|Approved|Submitted|Rejected|Archived",
  "actor": "string",
  "payload": {}
}
```

Invalid transitions return `400`. Missing applications return `404`. The `Submitted` transition is
guarded by submission evidence recorded through policy and executor activity.

### `POST /applications/{application_id}/score`

Records deterministic application scoring.

```json
{
  "actor": "string"
}
```

Returns the updated `ApplicationRead`. Missing applications return `404`.

### `POST /applications/{application_id}/policy-decisions`

Evaluates and records a policy decision before executor dispatch.

```json
{
  "requested_action": "string",
  "worker": "email|browser|documents|string",
  "mode": "dry_run",
  "context": {
    "confidence": "high|medium|low|string",
    "fit_score": 0,
    "recommendation": "recommended|needs_review|not_recommended|string",
    "reasons": [],
    "risks": [],
    "missing_data": [],
    "red_flags": []
  },
  "actor": "string"
}
```

If `context` is null, the backend derives policy context from stored application scoring fields.
Missing applications return `404`; incompatible stored automation or confidence values return `400`.

### `POST /applications/{application_id}/executor-actions/dry-run`

Plans an executor action without external side effects and records audit evidence.

```json
{
  "policy_decision_id": "uuid",
  "action_type": "string",
  "idempotency_key": "string",
  "payload": {},
  "worker": "email|browser|documents|string",
  "actor": "string"
}
```

Missing applications return `404`. Missing, mismatched, or denied policy decisions return `400`.

### `POST /applications/{application_id}/packet-reviews`

Records a human packet review decision.

```json
{
  "decision": "approved|rejected|changes_requested",
  "reviewed_by": "string",
  "source": "dashboard",
  "packet_text": "string|null",
  "notes": "string|null"
}
```

Returns the persisted packet review. Missing applications return `404`.

## Read Endpoints

### `GET /applications/{application_id}/events`

Returns append-only event rows for an application. Missing applications return `404`.

### `GET /applications/{application_id}/audit`

Returns the full dashboard audit bundle:

```json
{
  "application": {},
  "events": [],
  "policy_decisions": [],
  "executor_actions": []
}
```

Missing applications return `404`.

### `GET /applications/{application_id}/review-summary`

Returns the compact reviewer-facing workflow summary:

```json
{
  "application": {},
  "latest_policy_decision": {},
  "latest_executor_action": {},
  "latest_packet_review": {},
  "packet_reviews": [],
  "event_count": 0,
  "next_states": [],
  "ready_for_policy": false,
  "ready_for_dry_run": false,
  "ready_for_submission": false
}
```

Missing applications return `404`.

## Compatibility Notes

- `company` remains a dashboard-compatible display string projected from the M3 company identity
  model.
- `company_source_text` is raw intake provenance and must not become canonical company truth.
- The dashboard currently consumes `/jobs`, `/applications`, state updates, scoring, policy
  decisions, dry-run executor actions, packet reviews, audit summaries, and review summaries.
- This contract intentionally excludes future list/update/delete packet review APIs, document
  versioning APIs, recruiter communication APIs, and real external execution APIs.
