# State Transition Validation Sequence

```mermaid
sequenceDiagram
    participant Caller as API/Service Caller
    participant Machine as ApplicationStateMachine
    participant Rules as ALLOWED_TRANSITIONS
    participant Tracker as Application Tracker
    participant Log as Event Log

    Caller->>Machine: apply_transition(current, target)
    Machine->>Rules: can_transition(current, target)
    Rules-->>Machine: allowed or denied

    alt transition allowed
        Machine-->>Caller: target state
        Caller->>Tracker: persist state update
        Tracker->>Log: application.state_changed
    else transition denied
        Machine-->>Caller: InvalidStateTransitionError
        Caller-->>Caller: keep current state
    end
```

## Invariants
- Callers must validate transitions through the state machine boundary.
- Invalid transitions do not mutate application state.
- Persisted state changes must emit an append-only event log entry.
- Policy and executor flows remain separate contracts layered around this transition boundary.
