# Application State Models

## Implemented M1 State Machine

```mermaid
stateDiagram-v2
    [*] --> ApplicationCreated
    ApplicationCreated --> Draft

    Draft --> ReadyForReview
    Draft --> Archived

    ReadyForReview --> Approved
    ReadyForReview --> Rejected
    ReadyForReview --> Draft

    Approved --> Submitted
    Approved --> Rejected

    Submitted --> Archived
    Rejected --> Archived

    Archived --> [*]
```

## Transition Table

| Current state | Allowed next states |
| --- | --- |
| `ApplicationCreated` | `Draft` |
| `Draft` | `ReadyForReview`, `Archived` |
| `ReadyForReview` | `Approved`, `Rejected`, `Draft` |
| `Approved` | `Submitted`, `Rejected` |
| `Submitted` | `Archived` |
| `Rejected` | `Archived` |
| `Archived` | None |

## M1 Rules

- New applications start in `ApplicationCreated`.
- `Archived` is terminal.
- Invalid transitions are rejected by `ApplicationStateMachine.apply_transition`.
- The source of truth for allowed transitions is `ALLOWED_TRANSITIONS`.

## Proposed Future Headline Projection - Not Implemented

This diagram explains how the locked PDF vocabulary can be projected from independent lifecycle,
packet, submission, conversation, and review evidence. It is not a database enum or an authorized
migration.

```mermaid
stateDiagram-v2
    [*] --> discovered
    discovered --> parsed: normalized job evidence
    parsed --> scored: scoring evidence
    scored --> packet_ready: packet ready
    scored --> review_needed: review required
    packet_ready --> review_needed: review required
    packet_ready --> form_filled: approved path
    review_needed --> packet_ready: packet review resolved
    review_needed --> form_filled: submission review resolved
    form_filled --> review_needed: execution blocked
    form_filled --> applied: successful submission evidence
    applied --> interview: recruiter or human evidence
    scored --> rejected_archived: not recommended or human decision
    applied --> rejected_archived: rejection or archive
    interview --> rejected_archived: rejection or archive
```

Binding proposed values, transitions, actors, evidence, and failure behavior are recorded in
`docs/decisions/ADR-0006-lifecycle-state-model.md` and
`docs/contracts/lifecycle-transition-contract.md`.
