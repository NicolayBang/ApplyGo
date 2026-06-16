# Component Diagram

```mermaid
flowchart LR
    UI[Frontend Dashboard] --> API[Backend API]
    API --> TRK[Tracker / Unit of Work]
    API --> POL[Policy Engine]
    API --> SM[State Machine]
    API --> EXE[Executor Contract]

    TRK --> DB[(PostgreSQL)]
    TRK --> EVT[Event Log]
    TRK --> CID[Company Identity]
    TRK --> PREV[Packet Review Records]

    EXE -. future worker contract .-> W1[Email Worker]
    EXE -. future worker contract .-> W2[Browser Worker]
    EXE -. future worker contract .-> W3[Document Worker]

    Q[(Redis Queue)] -. future orchestration .-> W1
    Q -. future orchestration .-> W2
    Q -. future orchestration .-> W3

    POL --> EVT
    EXE --> EVT
    SM --> EVT
```

## Notes
- Workflow owns state transitions.
- Database remains canonical source of truth.
- Workers only execute approved structured commands.
- Dry-run and execute share the same executor contract.
- Company identity and packet review persistence are implemented inside the current monolith.
- Worker implementations and Redis-backed orchestration remain later-phase contracts/stubs.
