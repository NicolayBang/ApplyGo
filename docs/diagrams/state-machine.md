# Application State Machine

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
