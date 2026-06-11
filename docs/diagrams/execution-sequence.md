# Policy and Execution Sequence

```mermaid
sequenceDiagram
    participant A as Action Request
    participant P as Policy Engine
    participant L as Event Log
    participant E as Executor Contract
    participant W as Worker
    participant T as Tracker/State Machine

    A->>P: Evaluate(request, mode, context)
    P->>L: policy_decision_logged
    alt decision == allow
        P->>E: Invoke(request)
        E->>L: executor_attempt_logged
        alt mode == dry_run
            E-->>W: Plan only (no side effect)
            W-->>E: planned
        else mode == execute
            E->>W: Perform action
            W-->>E: completed/failed
        end
        E->>L: executor_result_logged
        E->>T: update_state
        T->>L: state_updated
    else decision == deny/review
        P->>T: transition blocked_by_policy or review_needed
        T->>L: state_updated
    end
```

## Invariants
- Policy decision is logged before any executor call.
- Dry-run and execute use identical command shape.
- Idempotency key is required for executor actions.