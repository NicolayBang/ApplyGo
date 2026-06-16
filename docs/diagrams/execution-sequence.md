# Workflow Validation Sequences

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

```mermaid
sequenceDiagram
    participant Reviewer as Reviewer / Dashboard
    participant API as Backend API
    participant Tracker as Tracker
    participant Reviews as Packet Review Table
    participant Log as Event Log

    Reviewer->>API: POST /applications/{id}/packet-reviews
    API->>Tracker: record_packet_review(application_id, data)
    Tracker->>Reviews: insert packet review row
    Tracker->>Log: application_packet.reviewed
    API-->>Reviewer: ApplicationPacketReviewRead
```

```mermaid
sequenceDiagram
    participant Reviewer as Reviewer / Dashboard
    participant API as Backend API
    participant Tracker as Tracker
    participant Policy as Allowed Policy Decisions
    participant Exec as Executor Evidence
    participant Log as Event Log

    Reviewer->>API: PATCH /applications/{id}/state Submitted
    API->>Tracker: submit_application(application_id, actor, payload)
    Tracker->>Policy: verify allowed policy decision exists
    Tracker->>Exec: verify executor evidence matches allowed policy

    alt prerequisites satisfied
        Tracker->>Log: application.state_changed
        API-->>Reviewer: ApplicationRead(state=Submitted)
    else prerequisites missing
        API-->>Reviewer: 400 InvalidStateTransitionError
    end
```

## Invariants
- Callers must validate transitions through the state machine boundary.
- Invalid transitions do not mutate application state.
- Persisted state changes must emit an append-only event log entry.
- Packet review decisions persist as reviewer evidence and append `application_packet.reviewed`.
- `Submitted` requires the dedicated submit workflow plus allowed policy and matching executor evidence.
- Packet review evidence is exposed through the review summary, but it is not yet a database-enforced
  submission prerequisite.
