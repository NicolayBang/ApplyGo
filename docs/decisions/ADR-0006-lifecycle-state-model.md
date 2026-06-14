# ADR-0006-lifecycle-state-model

## Status

Proposed

## Date

2026-06-14

## Context

The locked architecture PDF describes a product workflow with `discovered`, `parsed`, `scored`,
`packet_ready`, `review_needed`, `form_filled`, `applied`, `interview`, and
`rejected/archived` stages.

The implemented M1 workflow intentionally uses a smaller control-plane enum:
`ApplicationCreated`, `Draft`, `ReadyForReview`, `Approved`, `Submitted`, `Rejected`, and
`Archived`.

The M1 enum is current database and API truth. Replacing it directly with the PDF vocabulary would
mix independent concerns:

- broad application lifecycle;
- packet generation and approval;
- form filling and submission;
- recruiter conversation;
- temporary human-review requirements.

ADR-0002 already defers lifecycle substates until a dedicated ADR reconciles this boundary.

## Decision

Adopt, as a proposed future direction, independent persisted state dimensions:

| Dimension | Proposed values | Default |
|---|---|---|
| `applications.lifecycle_state` | `discovered`, `active`, `applied`, `interview`, `rejected`, `archived` | `discovered` |
| `applications.packet_state` | `not_started`, `drafting`, `ready`, `needs_review`, `approved`, `failed` | `not_started` |
| `applications.submission_state` | `not_started`, `form_filled`, `needs_review`, `approved`, `submitted`, `failed`, `blocked` | `not_started` |
| `threads.conversation_state` | `none`, `active`, `awaiting_candidate`, `awaiting_recruiter`, `closed` | `none` |

Parsing and scoring remain evidence-bearing processing milestones rather than new persistent state
columns. Their completion is derived from persisted normalized job data, scoring outputs, and audit
events.

`review_needed` is a derived condition, not a durable headline lifecycle value. It is true when a
policy decision, packet, submission, or communication requires unresolved human action.

The user-facing headline state is derived, not independently mutable. Proposed precedence:

1. `archived`
2. `rejected`
3. `interview`
4. `applied`
5. `review_needed`
6. `form_filled`
7. `packet_ready`
8. `scored`
9. `parsed`
10. `discovered`

The exact derivation inputs and transition rules are defined in
`docs/contracts/lifecycle-transition-contract.md`.

## Compatibility Boundary

- Current `applications.state` remains the implemented M1 source of truth.
- This ADR does not rename, remove, reinterpret, or add any database column.
- Existing API and dashboard state values remain unchanged until a separate migration and
  compatibility contract is approved.
- Backfill from the M1 enum is intentionally conservative and may not infer packet or submission
  progress without persisted evidence.
- Any implementation must support a compatibility period in which old consumers continue reading
  the M1 state field or an explicitly documented projection.

## Architecture Mapping

| PDF stage | Proposed source |
|---|---|
| `discovered` | `lifecycle_state=discovered` |
| `parsed` | required normalized job evidence and parse event |
| `scored` | persisted score/recommendation evidence and score event |
| `packet_ready` | `packet_state=ready` or `approved` |
| `review_needed` | unresolved persisted review requirement |
| `form_filled` | `submission_state=form_filled` or `approved` |
| `applied` | `lifecycle_state=applied` and `submission_state=submitted` |
| `interview` | `lifecycle_state=interview` |
| `rejected/archived` | `lifecycle_state=rejected` or `archived` |

## Implementation Entry Conditions

Implementation remains blocked until:

1. Nicolay and Francis approve this ADR and the lifecycle transition contract.
2. A schema migration contract defines columns, checks, backfill, rollback, and deletion behavior.
3. An API/dashboard compatibility contract defines old and new state projections.
4. Event vocabulary and audit payload changes are approved.
5. Runnable tests cover transitions, invalid transitions, policy evidence, execution evidence,
   review resolution, compatibility, and PostgreSQL constraints.

## Consequences

### Positive

- The PDF workflow can be represented without one overloaded enum.
- Packet, submission, and recruiter conversation can evolve independently.
- Review requirements remain auditable conditions rather than ambiguous lifecycle states.
- Database truth remains queryable without reconstructing state from event replay.

### Costs

- A future migration and compatibility period are required.
- Headline state becomes a deterministic projection that needs contract tests.
- Existing M1 approval semantics cannot be blindly mapped to packet or submission approval.

## Supersedes

None.

## Superseded by

None.
