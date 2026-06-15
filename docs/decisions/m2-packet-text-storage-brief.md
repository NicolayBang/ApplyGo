# M2 Packet Text Storage Brief

**Status:** Proposed review brief
**Decision needed:** Whether M2 should persist full packet text.
**Decision owners:** Nicolay + Francis
**Related:** `docs/contracts/m2-application-packet-contract.md`

## Plain-English Decision

When a human reviews an application packet, should ApplyPilot store the full generated packet text,
or should it only store the review decision and regenerate packet text from current evidence?

## Current State

The dashboard can generate, copy, and download deterministic packet text from existing application,
job, score, policy, executor, and audit evidence. This is read-only and does not create database
records.

## Options

### Option A: Store Full Packet Text

Store the packet text that the reviewer saw.

Pros:

- strongest historical snapshot;
- review evidence is easier to reproduce exactly;
- useful if packet text changes over time.

Cons:

- stores more potentially sensitive content;
- needs clearer privacy/export/deletion policy later;
- may duplicate data already available in application evidence;
- increases migration and API surface.

### Option B: Store Review Decision Only

Store the decision, reviewer, source, notes, and audit event. Regenerate packet text from current
evidence when needed.

Pros:

- smaller and simpler data model;
- avoids persisting large text blobs early;
- keeps M2 focused on review workflow, not document retention;
- lower privacy and storage risk.

Cons:

- exact reviewed text may not be reconstructable if evidence changes later;
- less useful for a strict audit snapshot.

### Option C: Store Optional Packet Text

Allow `packet_text` to be nullable. The dashboard may submit it later, but the first implementation
can leave it empty.

Pros:

- preserves future flexibility;
- lets M2 start with decision persistence only;
- avoids forcing a storage policy before the product proves need.

Cons:

- nullable behavior must be documented clearly;
- API clients need to know whether text is present.

## Recommendation

Choose **Option C: optional packet text**, but start M2 implementation with decision persistence
only unless exact text snapshots become necessary.

Reasoning:

- M2 needs to prove human packet review, not full document archival.
- Optional text keeps the schema flexible without committing to storing every generated artifact.
- The event log should record the decision, not the entire packet body.

## Suggested Implementation Constraint

If optional packet text is approved:

- keep `packet_text` nullable;
- do not require packet text for a valid review decision;
- do not include full packet text in event payloads;
- add tests proving a review can be recorded with `packet_text = null`;
- document any future change that makes packet text required.

## Decision To Record

Before implementation, record:

- whether `packet_text` is nullable;
- whether the first dashboard implementation sends packet text;
- whether exported/downloaded packets are user-owned local artifacts only;
- when exact packet snapshots become required.
