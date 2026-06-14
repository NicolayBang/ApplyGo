# Lifecycle Transition Contract

**Status:** Proposed

**Scope:** Future lifecycle, packet, submission, conversation, review, and headline-state behavior

**Does not authorize implementation:** Yes

**Related:** `docs/decisions/ADR-0006-lifecycle-state-model.md`,
`docs/architecture/OpenClaw_Final_Agreed_Architecture.pdf`,
`docs/contracts/event-log-contract.md`, `docs/contracts/policy-contract.md`,
`docs/contracts/executor-contract.md`

## Current Binding Baseline

Until this contract and its migration/compatibility work are approved and implemented:

- `applications.state` remains the only persisted application workflow state;
- the implemented M1 transition table remains binding;
- `Tracker.update_state()` and `Tracker.submit_application()` remain the workflow boundaries;
- no new lifecycle column, state value, event name, or API field is authorized.

## Proposed State Dimensions

The values and defaults are defined by ADR-0006:

- lifecycle: `discovered`, `active`, `applied`, `interview`, `rejected`, `archived`;
- packet: `not_started`, `drafting`, `ready`, `needs_review`, `approved`, `failed`;
- submission: `not_started`, `form_filled`, `needs_review`, `approved`, `submitted`, `failed`,
  `blocked`;
- conversation: `none`, `active`, `awaiting_candidate`, `awaiting_recruiter`, `closed`.

## Allowed Transitions

### Lifecycle

| Current | Allowed next |
|---|---|
| `discovered` | `active`, `rejected`, `archived` |
| `active` | `applied`, `rejected`, `archived` |
| `applied` | `interview`, `rejected`, `archived` |
| `interview` | `rejected`, `archived` |
| `rejected` | `archived` |
| `archived` | none |

### Packet

| Current | Allowed next |
|---|---|
| `not_started` | `drafting` |
| `drafting` | `ready`, `needs_review`, `failed` |
| `ready` | `needs_review`, `approved`, `drafting` |
| `needs_review` | `approved`, `drafting` |
| `approved` | `drafting` |
| `failed` | `drafting` |

An approved packet may return to `drafting` only as a new version; prior approved versions remain
immutable audit evidence.

### Submission

| Current | Allowed next |
|---|---|
| `not_started` | `form_filled`, `needs_review`, `blocked`, `failed` |
| `form_filled` | `needs_review`, `approved`, `blocked`, `failed` |
| `needs_review` | `form_filled`, `approved`, `blocked` |
| `approved` | `submitted`, `blocked`, `failed` |
| `submitted` | none |
| `blocked` | `not_started`, `form_filled`, `needs_review` |
| `failed` | `not_started`, `form_filled`, `needs_review`, `blocked` |

### Conversation

| Current | Allowed next |
|---|---|
| `none` | `active` |
| `active` | `awaiting_candidate`, `awaiting_recruiter`, `closed` |
| `awaiting_candidate` | `awaiting_recruiter`, `closed` |
| `awaiting_recruiter` | `awaiting_candidate`, `closed` |
| `closed` | `active` |

Reopening a closed conversation requires a new provider message or explicit human action.

## Actors And Authority

| Actor | May propose or perform |
|---|---|
| Human user/reviewer | Approvals, rejections, archives, review resolution, explicit reopening |
| Workflow service | Deterministic transitions after required evidence is persisted |
| Parser/scorer | Persist parse/score evidence; may propose lifecycle activation, never permission |
| Document worker | Packet transitions through executor evidence |
| Browser worker | Submission transitions through executor evidence |
| Email worker/provider sync | Conversation transitions and proposed lifecycle outcomes |
| Policy engine | Permission decision only; never directly mutates workflow state |
| LLM | Extraction, classification, scoring support, or drafting only; never permission or state |

Workers and LLMs must not write state columns directly.

## Preconditions And Evidence

- Every transition validates the current persisted value and allowed target.
- A transition caused by external execution requires:
  1. policy check;
  2. persisted policy decision;
  3. executor attempt;
  4. persisted executor result;
  5. workflow transition and transition event.
- `submission_state=submitted` additionally requires a successful result that identifies the
  submission target and stable idempotency key.
- `lifecycle_state=applied` requires `submission_state=submitted`.
- `lifecycle_state=interview` requires persisted recruiter/provider evidence or explicit human
  confirmation.
- `packet_state=approved` and `submission_state=approved` require a persisted human approval unless
  a later full-auto policy contract explicitly permits the action.
- Clearing `needs_review` requires a persisted review resolution or override; a new policy decision
  does not erase the earlier decision.
- `rejected` and `archived` require a reason and actor in the transition payload.

## Proposed Event Vocabulary

Implementation must amend the event log contract before introducing:

- `application.lifecycle_state_changed`
- `application.packet_state_changed`
- `application.submission_state_changed`
- `thread.conversation_state_changed`
- `application.review_required`
- `application.review_resolved`
- `application.transition_rejected`

Each state-change event includes dimension, from/to values, actor, reason, correlation ID, policy
decision ID where applicable, executor action ID where applicable, and occurred-at timestamp.
Before M7, the event contract must define how a thread-owned event references one or more related
applications without duplicating or losing audit evidence.

## Failure Behavior

- Invalid transitions do not mutate current state.
- Policy denial records the decision and leaves state unchanged; it may create a review requirement.
- Executor failure is logged before any resulting state change.
- Failed or blocked execution must never produce `submitted` or `applied`.
- Unknown provider signals are stored as evidence and routed to review; they do not mutate lifecycle.
- Replayed or duplicate signals reuse idempotent results and must not append duplicate state changes.
- Partial multi-dimension updates are prohibited. Required related changes commit atomically with
  their audit events.

## Derived Headline State

The headline is computed from persisted dimensions and evidence using ADR-0006 precedence. It is
read-only and must not be accepted as a write target.

`parsed` and `scored` are emitted only when their required persisted evidence exists.
`review_needed` takes precedence over packet/form progress but not over terminal outcomes,
interview, or applied.

## M1 Compatibility Mapping

This mapping is a planning aid, not an approved backfill:

| M1 state | Conservative future interpretation |
|---|---|
| `ApplicationCreated` | lifecycle `discovered`; packet/submission `not_started` |
| `Draft` | lifecycle `active`; no packet/submission progress inferred |
| `ReadyForReview` | lifecycle `active`; unresolved review requirement |
| `Approved` | lifecycle `active`; approval evidence retained, target dimension not inferred |
| `Submitted` | lifecycle `applied`; submission `submitted` only with matching executor evidence |
| `Rejected` | lifecycle `rejected` |
| `Archived` | lifecycle `archived` |

## Implementation And Test Gate

Before implementation:

- approve ADR-0006 and this contract;
- approve schema migration and API compatibility contracts;
- update policy, executor, event, database, and privacy contracts as applicable;
- test every allowed and rejected transition;
- test policy/executor ordering and atomic event persistence;
- test duplicate signals and idempotent replay;
- test M1 compatibility projections and representative backfill data;
- test PostgreSQL value constraints and rollback limits.
