# M2 Application Packet Contract

**Status:** Draft contract for M2 review
**Milestone:** M2
**Does not authorize migration:** Yes

This contract defines the first M2 application packet boundary. It is intentionally narrower than
the future M5 document/version/answer model described in ADR-0002 and the database roadmap.

## Purpose

M2 should give a human reviewer a clear packet of application material before any external
automation exists.

The packet should answer:

- What application is being reviewed?
- What evidence supports or weakens the application?
- What content could a human use next?
- What is still missing or requires review?
- What audit evidence exists?

## M2 Packet Definition

An M2 application packet is a reviewer-facing aggregate assembled from current M1 data:

```text
application
-> job
-> scoring evidence
-> latest policy decision
-> latest dry-run executor result, when present
-> audit/event summary
-> deterministic packet text, when generated
```

The first implementation should prefer a read-only or generated-on-demand packet preview. Persisted
packet records require additional review.

## Allowed First Slice

The first M2 implementation may:

- render a packet preview in the dashboard;
- use existing job and application fields;
- include score, confidence, recommendation, reasons, risks, missing data, and red flags;
- include latest policy decision summary;
- include latest dry-run executor result summary;
- generate deterministic human-readable packet text from existing data;
- expose copyable text for human use;
- add frontend tests or dashboard asset contract tests.

The first slice should not require a database migration.

## Persistence Gate

Before persisting packet data, approve a follow-up implementation contract that defines:

- whether the current `documents` table is enough for M2;
- allowed `doc_type` values;
- whether `content`, `content_json`, or both are required;
- event names for packet generation, review, approval, and rejection;
- retention and delete behavior;
- API endpoints and response schemas;
- tests proving persistence and audit behavior.

Until this is approved, packet preview may be generated from existing API data without writing new
records.

Proposed persistence direction is documented in
`docs/contracts/m2-packet-persistence-contract.md`. That proposal requires Nicolay + Francis review
before implementation.

## Current `documents` Boundary

The M1 `documents` table is an application-owned placeholder:

```text
documents.application_id -> applications.id ON DELETE CASCADE
documents.doc_type
documents.content
documents.content_json
documents.version
```

It is valid for M1 placeholders, but it is not the future reusable document/version model.

M2 may use it only after review confirms that single-application ownership and cascade behavior are
acceptable for the specific M2 packet artifact. If packet artifacts become audit-bearing decisions,
their retention behavior must be reviewed before implementation.

## Explicitly Deferred

This contract does not approve:

- `document_versions`;
- `application_documents`;
- `answer_library`;
- `application_answers`;
- company normalization;
- Gmail sending;
- browser automation;
- real external submission;
- LLM-required happy paths;
- production deployment.

The deferred document/version/answer entities are now described as **Proposed / Not Implemented** in
`docs/contracts/m5-packet-document-answer-contract.md`. That M5 contract does not change this M2
boundary: M2 remains a reviewer-facing, review-only packet aggregate, and the M5 versioned model
authorizes nothing until Nicolay and Francis approve it.

## Packet Preview Shape

A non-persisted packet preview may use this shape:

```json
{
  "application_id": "uuid",
  "job": {
    "title": "string|null",
    "company": "string|null",
    "location": "string|null",
    "source_url": "string|null",
    "job_type": "string|null",
    "salary_raw": "string|null"
  },
  "score": {
    "fit_score": 0,
    "confidence": "high|medium|low|null",
    "recommendation": "recommended|needs_review|not_recommended|null",
    "reasons": [],
    "risks": [],
    "missing_data": [],
    "red_flags": []
  },
  "policy": {
    "decision": "allow|deny|review|null",
    "allowed": false,
    "required_overrides": []
  },
  "executor": {
    "execution_mode": "dry_run|null",
    "status": "planned|completed|failed|blocked|null",
    "side_effects": false,
    "planned_steps": [],
    "requires": []
  },
  "packet_text": "string"
}
```

This shape is a frontend/view contract for the first slice. It is not a database schema.

## Deterministic Packet Text Rules

Generated packet text must be deterministic for the same input.

It may include:

- role and company summary;
- fit score and recommendation;
- strongest reasons;
- risks and missing data;
- policy decision summary;
- dry-run executor summary;
- clear next human action.

It must not:

- claim that an application was submitted;
- claim that email or browser automation ran;
- invent job facts;
- hide missing data;
- require an LLM to complete the happy path.

## Audit Expectations

For the first read-only packet preview, no audit event is required.

If a future PR persists packet generation or human review decisions, it must define and test event
names before merge. Candidate event names should use the existing implemented vocabulary style, for
example:

```text
application_packet.generated
application_packet.reviewed
application_packet.approved
application_packet.rejected
```

Do not add these events until implementation exists.

## Validation Expectations

Frontend-only preview:

- `npm run typecheck`
- `npm run test`
- `npm run build`
- relevant dashboard asset contract tests
- manual dashboard inspection when layout changes

Backend or persistence:

- backend lint
- pytest
- PostgreSQL-backed validation if migrations or DB behavior change
- tests for packet generation and audit events

## Review Rule

If implementation needs persistence, migration, new event names, or policy/executor changes, stop
and request Nicolay and Francis review before coding.
