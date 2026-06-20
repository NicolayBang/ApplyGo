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
- This contract intentionally excludes future list/update/delete packet review APIs, recruiter
  communication APIs, and real external execution APIs from the implemented boundary.
- The document/answer/packet-read-model resources below are recorded only as a **Proposed M5 API —
  Not Implemented** design and authorize no endpoint.

## Proposed M5 API — Not Implemented

**Status:** Proposed / Not Implemented. This section authorizes no endpoint, route handler, or
frontend change. It records the future HTTP surface for the M5 document/answer/packet model defined
in `docs/contracts/m5-packet-document-answer-contract.md`, which requires explicit Nicolay + Francis
approval before any implementation.

All endpoints below are additive. They must preserve every implemented route, the implemented M2
packet-review boundary, and the dashboard types in `frontend/app/src/api/types.ts`. None of them
performs an external side effect, and none authorizes a delete endpoint or cascade behavior. M5
remains a single workspace, so no request or response field carries `user_id`, account, or tenancy
data.

### Document library and immutable versions (proposed)

```text
POST   /documents                          # create a reusable logical document (doc_type, name)
GET    /documents                          # list non-archived documents; archived excluded by default
GET    /documents/{document_id}            # read one logical document
POST   /documents/{document_id}/archive    # set is_archived = true (no delete)
POST   /documents/{document_id}/versions   # append an immutable version (content and/or content_json)
GET    /documents/{document_id}/versions   # list immutable versions ordered by version_number
GET    /document-versions/{version_id}     # read one immutable version (version_number, checksum)
```

Proposed behavior:

- `doc_type` and version payloads are validated; invalid `doc_type`, blank `name`, non-positive
  version, or a version with neither `content` nor `content_json` return `400`.
- Document versions are immutable: there is no update or delete route. A correction appends a new
  version.
- Missing `document_id`/`version_id` return `404`.

### Answer library (proposed)

```text
POST   /answers                  # create a reusable answer (question_key, question_text, answer_text)
GET    /answers                  # list non-archived library answers
GET    /answers/{answer_id}      # read one library answer
PATCH  /answers/{answer_id}      # edit current question_text/answer_text in place
POST   /answers/{answer_id}/archive   # set is_archived = true (no delete)
```

Proposed behavior:

- A duplicate active `question_key` (a non-archived row already using the key) returns `409`.
- Editing or archiving a library answer never alters any historical `application_answers` snapshot.
- Missing `answer_id` returns `404`.

### Application document attachments and answer snapshots (proposed)

```text
POST   /applications/{application_id}/documents   # attach an EXACT document_version_id (role, display_order)
GET    /applications/{application_id}/documents   # list attachments ordered by display_order
POST   /applications/{application_id}/answers      # record an immutable answer snapshot (optional answer_library_id)
GET    /applications/{application_id}/answers       # list immutable answer snapshots
```

Proposed behavior:

- An attachment binds an exact `document_version_id` and never silently upgrades to a later version;
  attaching a newer version is a new request.
- A reference to a missing application, document version, or answer library row returns `400`
  (invalid reference); a missing application path returns `404`.
- Attachments and answer snapshots are append-only; there is no update or delete route.
- Recording an answer snapshot may carry optional `answer_library_id` provenance only.

### Application packet read model (proposed)

```text
GET    /applications/{application_id}/packet
```

Proposed response combines exact version projections, immutable answer snapshots, and the current M2
review evidence:

```json
{
  "application": {},
  "documents": [
    {
      "application_document_id": "uuid",
      "document_id": "uuid",
      "document_version_id": "uuid",
      "role": "resume|cover_letter|supporting|other",
      "version_number": 1,
      "checksum": "string",
      "display_order": 0
    }
  ],
  "answers": [
    {
      "application_answer_id": "uuid",
      "answer_library_id": "uuid|null",
      "question_key": "string",
      "question_text": "string",
      "answer_text": "string"
    }
  ],
  "latest_packet_review": {}
}
```

Proposed compatibility and error behavior:

- Document entries project the **exact** attached `version_number` and `checksum`, ordered
  deterministically by `display_order`, then `created_at`, then `id`.
- Answer entries project immutable `application_answers` snapshots, never re-derived from the mutable
  `answer_library`.
- `latest_packet_review` reuses the implemented M2 review evidence and does not replace or weaken the
  review-only boundary.
- The read model is additive and compatible: an application with no M5 documents or answers returns
  empty lists, and existing dashboard responses are unaffected.
- A missing application returns `404`.
