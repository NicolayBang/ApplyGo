# M2 Packet Persistence Contract

**Status:** Implemented M2 baseline
**Milestone:** M2
**Authorizes migration:** Historical authorization only
**Authorizes implementation:** Historical authorization only

This contract defines the decision boundary for persisting M2 application packet review decisions.
It records the contract that the implemented M2 packet review slice now follows. It does not
authorize additional packet storage, document versioning, external automation, or future schema
expansion by itself.

## Implementation Status

The M2 baseline implementation now includes:

- `application_packet_reviews` persistence;
- `application_packet.reviewed` audit events;
- `POST /applications/{application_id}/packet-reviews`;
- `latest_packet_review` exposure through the review summary;
- dashboard controls for approve, reject, and request-changes decisions.

The implemented dashboard path records the review decision, reviewer, source, and optional notes.
It does not send full packet text by default, send email, open browser automation, submit an
application, call an LLM, or require OpenClaw.

## Purpose

The read-only packet preview is now useful for manual review. The next durable M2 step is to record
whether a human reviewed, approved, rejected, or requested changes to the prepared packet.

The persistence layer should answer:

- Who reviewed the packet?
- What decision did they make?
- What packet text or evidence was reviewed?
- What changed in the audit trail?
- Can the decision be explained later without relying on transient UI state?

## Implemented Scope

The first persistence implementation records packet review decisions only.

Allowed persisted artifact:

```text
application_packet.reviewed
```

Allowed decision values:

```text
approved | rejected | changes_requested
```

Allowed source:

```text
dashboard
```

## Storage Direction

Use a dedicated table rather than overloading the existing M1 `documents` placeholder.

Rationale:

- packet review decisions are audit-bearing workflow records;
- the current `documents` table is application-owned and cascade-deletes with the application;
- reviewer decisions should be easier to query than generic document blobs;
- M2 does not need the future reusable document/version model yet.

Table name:

```text
application_packet_reviews
```

Fields:

```text
id uuid PK
application_id uuid FK -> applications.id
decision varchar(32)
reviewed_by varchar(64)
source varchar(32)
packet_text text nullable
notes text nullable
created_at timestamptz
```

Retention:

- Do not cascade-delete packet review rows from ORM relationships.
- Database delete behavior must be reviewed with the migration PR.
- Event log remains the append-only audit source.

## API Boundary

Endpoint:

```text
POST /applications/{application_id}/packet-reviews
```

Request shape:

```json
{
  "decision": "approved",
  "reviewed_by": "human",
  "source": "dashboard",
  "packet_text": "string|null",
  "notes": "string|null"
}
```

Response shape:

```json
{
  "id": "uuid",
  "application_id": "uuid",
  "decision": "approved",
  "reviewed_by": "human",
  "source": "dashboard",
  "packet_text": "string|null",
  "notes": "string|null",
  "created_at": "datetime"
}
```

## Audit Event

Persisting a packet review decision must append this event:

```text
application_packet.reviewed
```

Payload should include:

```json
{
  "packet_review_id": "uuid",
  "decision": "approved",
  "reviewed_by": "human",
  "source": "dashboard"
}
```

Do not log full packet text in the event payload by default. Store full text only on the packet
review row if the implementation chooses to persist it.

## Validation Requirements For Implementation

Any implementation PR must include runnable tests for:

- valid packet review decisions;
- invalid decision rejection;
- missing application returns 404;
- review row is persisted;
- `application_packet.reviewed` event is appended;
- audit summary or a dedicated read endpoint exposes review evidence, if implemented;
- PostgreSQL migration upgrade succeeds;
- existing M1 dashboard flow still passes.

## Explicitly Out Of Scope

This contract does not approve:

- document versioning;
- reusable document libraries;
- answer-library tables;
- Gmail sending;
- browser automation;
- OpenClaw execution;
- real application submission;
- LLM-required packet generation;
- company normalization or ADR-0005 implementation.

## Closeout Review

The implemented M2 baseline reflects these reviewed choices:

- dedicated table instead of the `documents` table;
- no ORM delete cascade from applications to packet review rows;
- nullable `packet_text`, with the dashboard not sending full packet text by default;
- dashboard review decisions are enough for the M2 baseline.

Future changes that persist full packet snapshots, add document versioning, change retention
behavior, or connect packet approval to external automation need a new review.
