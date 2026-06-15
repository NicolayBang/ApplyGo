# M2 Packet Review Audit Event Brief

**Status:** Proposed review brief
**Decision needed:** Audit event semantics for packet review decisions.
**Decision owners:** Nicolay + Francis
**Related:** `docs/contracts/event-log-contract.md`; `docs/contracts/m2-application-packet-contract.md`

## Plain-English Decision

What audit event should ApplyPilot write when a human records a packet review decision?

## Current State

M1 writes explicit audit events for application creation, scoring, policy decisions, executor
attempts, executor results, and state changes. M2 packet preview is currently read-only, so it does
not write audit events.

## Recommended Event

Use:

```text
application_packet.reviewed
```

Why:

- it matches the existing domain-prefixed event style;
- it describes the human review decision without implying submission or external automation;
- it can cover approved, rejected, and changes-requested outcomes;
- it keeps packet review separate from policy and executor events.

## Recommended Payload

```json
{
  "packet_review_id": "uuid",
  "decision": "approved",
  "reviewed_by": "human",
  "source": "dashboard"
}
```

Optional fields may include:

```json
{
  "notes_present": true,
  "packet_text_persisted": false
}
```

## Payload Boundaries

Do not include full packet text in the event payload by default.

Reasoning:

- event payloads should stay compact and audit-focused;
- packet text may contain sensitive job/application material;
- exact text storage should be decided separately from event semantics.

## Ordering

The implementation should write in one unit of work:

```text
persist packet review row
-> append application_packet.reviewed event
-> commit
```

Do not append the event without a durable review row if the approved implementation includes the
`application_packet_reviews` table.

## Read Model Expectation

The audit timeline should be able to show:

```text
Packet review: approved by human from dashboard
```

The dashboard does not need to display packet text from the event.

## Test Expectations

Implementation tests should prove:

- event is appended after a valid packet review;
- event references the packet review id;
- event payload includes decision, reviewer, and source;
- event payload does not include full packet text by default;
- invalid review decisions do not append events.

## Out Of Scope

This brief does not approve:

- policy behavior changes;
- executor behavior changes;
- state transition changes;
- storing full packet text in event payloads;
- external automation or real submission.
