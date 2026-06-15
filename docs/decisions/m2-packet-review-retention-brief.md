# M2 Packet Review Retention Brief

**Status:** Proposed review brief
**Decision needed:** Packet review retention behavior before implementation.
**Decision owners:** Nicolay + Francis
**Related:** `docs/contracts/m2-application-packet-contract.md`

## Plain-English Decision

When ApplyPilot records a human packet review decision, should that row be retained like audit
evidence or deleted with the application like the current M1 document placeholder?

This matters because packet review decisions explain what a human approved, rejected, or asked to
change before any external automation exists.

## Current State

M1 retains the core audit trail:

- policy decisions do not cascade-delete;
- executor actions do not cascade-delete;
- event log entries do not cascade-delete.

The current `documents` table is different. It is an application-owned placeholder and cascades with
the application. That is acceptable for temporary generated content, but less appropriate for
audit-bearing review decisions.

## Options

### Option A: Retain Packet Review Rows

Packet review rows survive application deletion attempts or use restrictive database behavior.

Pros:

- strongest audit posture;
- aligns with policy, executor, and event-log retention;
- preserves human decision evidence;
- easier to explain in a governed automation platform.

Cons:

- deletion behavior is stricter;
- implementation needs clear foreign-key and ORM rules;
- future cleanup workflows need more thought.

### Option B: Cascade Packet Review Rows With Application

Packet review rows delete when the application deletes.

Pros:

- simpler lifecycle;
- matches the current M1 `documents` placeholder;
- easier local cleanup.

Cons:

- weaker audit posture;
- review decisions can disappear;
- less consistent with governed workflow evidence.

### Option C: Store Only Event Evidence

Do not keep a packet review table long-term; rely on `application_packet.reviewed` events.

Pros:

- keeps fewer tables;
- event log remains the audit source.

Cons:

- harder to query current packet review status;
- event payloads should not contain full packet text;
- dashboard would need to reconstruct decision state from events.

## Recommendation

Choose **Option A: retain packet review rows** for M2 if packet review decisions are treated as
workflow evidence.

Reasoning:

- ApplyPilot's brand promise is control, transparency, and auditability.
- A packet approval is more like a policy decision than a disposable document draft.
- The dashboard can still keep packet text optional, but the decision itself should be durable.

## Suggested Implementation Constraint

If Option A is approved, the implementation PR should:

- avoid ORM delete cascade for packet review rows;
- use database behavior that prevents accidental loss of review evidence;
- add PostgreSQL-backed tests for delete/retention behavior;
- keep packet text optional until privacy and storage needs are clearer.

## Decision To Record

Before implementation, record:

- selected retention option;
- whether packet text is persisted;
- expected delete behavior;
- whether future cleanup/export tooling is needed before production use.
