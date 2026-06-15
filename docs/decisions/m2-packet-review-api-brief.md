# M2 Packet Review API Brief

**Status:** Proposed review brief
**Decision needed:** API shape for recording packet review decisions.
**Decision owners:** Nicolay + Francis
**Related:** `docs/contracts/m2-application-packet-contract.md`

## Plain-English Decision

What is the smallest API surface ApplyPilot needs to record a human packet review decision without
turning M2 into a document-management system?

## Current State

The dashboard currently generates packet text in the browser from existing audit data. Nothing is
persisted. The backend already has application-scoped routes for scoring, policy decisions, dry-run
executor actions, audit summaries, and review summaries.

## Options

### Option A: Create-Only Packet Review Endpoint

Add:

```text
POST /applications/{application_id}/packet-reviews
```

Pros:

- smallest useful API;
- matches the existing application-scoped route style;
- easy to test;
- records the human decision without adding review-management complexity.

Cons:

- no update workflow;
- no dedicated list/read endpoint unless audit or review summary exposes it.

### Option B: Full Packet Review Resource API

Add:

```text
POST /applications/{application_id}/packet-reviews
GET /applications/{application_id}/packet-reviews
GET /applications/{application_id}/packet-reviews/{packet_review_id}
PATCH /applications/{application_id}/packet-reviews/{packet_review_id}
```

Pros:

- richer product surface;
- easier future management of multiple reviews.

Cons:

- larger API before the product need is proven;
- update semantics are tricky for audit-bearing decisions;
- more tests and UI decisions required.

### Option C: Audit-Only Command

Add a command endpoint that writes only an event and no review table.

Pros:

- smallest persistence footprint;
- keeps event log as source of audit evidence.

Cons:

- harder to query current review status;
- weak dashboard support;
- event payload would carry too much product meaning.

## Recommendation

Choose **Option A: create-only packet review endpoint** for M2.

Reasoning:

- M2 needs to prove human packet review, not full document lifecycle management.
- Packet review decisions should be append-like, not frequently edited.
- A create-only command aligns with the governed workflow style already used for scoring, policy,
  and dry-run.

## Suggested Request Fields

```json
{
  "decision": "approved",
  "reviewed_by": "human",
  "source": "dashboard",
  "packet_text": null,
  "notes": null
}
```

## Suggested Response Fields

```json
{
  "id": "uuid",
  "application_id": "uuid",
  "decision": "approved",
  "reviewed_by": "human",
  "source": "dashboard",
  "packet_text": null,
  "notes": null,
  "created_at": "datetime"
}
```

## Suggested Read Surface

For the first implementation, prefer adding latest packet review evidence to the existing
review-summary or audit response only if the dashboard needs it immediately.

Avoid adding list/update/delete endpoints until product behavior requires them.

## Required Tests Before Merge

An implementation PR should test:

- valid create request returns 201;
- invalid decision returns 422 or 400;
- missing application returns 404;
- persisted row references the application;
- `application_packet.reviewed` event is appended;
- existing audit/review summary behavior remains compatible.

## Stop Conditions

Stop and request human review before adding:

- update or delete endpoints;
- document versioning;
- external automation;
- LLM-required review behavior;
- policy or executor behavior changes.
