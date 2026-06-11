# Component Diagram

```mermaid
flowchart LR
    UI[Frontend Dashboard] --> API[Backend API]
    API --> DB[(PostgreSQL)]
    API --> POL[Policy Engine]
    API --> SM[State Machine]
    API --> EVT[Event Log]
    API --> EXE[Executor Contract]

    EXE --> W1[Email Worker]
    EXE --> W2[Browser Worker]
    EXE --> W3[Document Worker]

    Q[(Redis Queue)] --> W1
    Q --> W2
    Q --> W3

    POL --> EVT
    EXE --> EVT
    SM --> EVT
```

## Notes
- Workflow owns state transitions.
- Database remains canonical source of truth.
- Workers only execute approved structured commands.
- Dry-run and execute share the same executor contract.