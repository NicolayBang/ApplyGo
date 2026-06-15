# M2 Packet Review Dashboard Boundary Brief

**Status:** Proposed review brief
**Decision needed:** Dashboard behavior for recording packet review decisions.
**Decision owners:** Nicolay + Francis
**Related:** `docs/capstone/m2-packet-preview-validation.md`; `docs/contracts/m2-application-packet-contract.md`

## Plain-English Decision

How should the dashboard let a human record a packet review decision without making the product feel
like it submitted an application or sent a message?

## Current State

The dashboard can display, copy, and download a deterministic packet preview. It does not persist a
review decision yet.

## Recommended UI Boundary

Add a small human-review control only after backend persistence exists.

Suggested actions:

```text
Approve packet
Request changes
Reject packet
```

Suggested supporting field:

```text
Reviewer notes
```

## Copy Guidelines

Use language that makes the boundary obvious:

- "Packet approved for manual use"
- "Packet needs changes"
- "Packet rejected"
- "This does not send email, open a browser, or submit an application"

Avoid language that implies external action:

- "Submit packet"
- "Send application"
- "Auto-apply"
- "Launch automation"

## Placement

Place the review control near the existing Application packet panel, after the packet text and copy
actions, so the reviewer sees the evidence before recording a decision.

Do not hide the audit timeline. Packet review should increase audit clarity, not replace it.

## Backend Dependency

Do not implement dashboard review controls until the backend can:

- persist the review decision;
- append `application_packet.reviewed`;
- return enough evidence for the dashboard to confirm the decision.

## Validation Expectations

Frontend implementation should prove:

- the controls are disabled or hidden until an application is loaded;
- valid decisions call the approved backend endpoint;
- success status makes clear no external side effect occurred;
- audit/review evidence refreshes after recording;
- packet copy/download behavior still works;
- mobile layout remains readable.

## Stop Conditions

Stop before UI implementation if it requires:

- policy behavior changes;
- executor behavior changes;
- state-machine changes;
- OpenClaw, Gmail, browser automation, or real submission;
- storing packet text before that storage decision is approved.

## Recommendation

Keep M2 dashboard review narrow: record the human packet decision and refresh audit evidence. Do not
make it a submission workflow.
