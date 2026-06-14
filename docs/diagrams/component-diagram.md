# Component Diagrams

## Implemented M1

```mermaid
flowchart LR
    UI[Static Review Dashboard] --> API[FastAPI Control Plane]
    API --> DB[(PostgreSQL)]
    API --> POL[Deterministic Policy Engine]
    API --> SM[M1 State Machine]
    API --> EVT[Append-only Event Log]
    API --> EXE[Executor Contract]
    EXE --> STUB[Dry-run Stub Executor]

    POL --> EVT
    EXE --> EVT
    SM --> EVT
```

Redis is provisioned by Compose, but no queue dispatcher or live outbound worker execution is
implemented in M1.

## Future Architecture - Planned / Not Implemented

```mermaid
flowchart LR
    UI[Review Dashboard and Overrides] --> API[Control Plane]
    API --> DB[(PostgreSQL)]
    API --> POL[Policy Engine]
    API --> SM[Workflow State Dimensions]
    API --> EVT[Event Log]
    API --> EXE[Executor Contract]
    API --> LLM[Constrained LLM Layer]

    EXE --> Q[(Redis-backed Delivery)]
    Q --> W1[Email Worker]
    Q --> W2[Browser Worker]
    Q --> W3[Document Worker]

    LLM --> API

    POL --> EVT
    EXE --> EVT
    SM --> EVT
```

## Notes
- Workflow owns state transitions.
- Database remains canonical source of truth.
- Workers only execute approved structured commands.
- Dry-run and execute share the same executor contract.
- Queue delivery, real workers, and LLM integration require their milestone contracts before
  implementation.
