# C4 Code Level: Workers — Documents

## Overview

- **Name**: Document Worker
- **Description**: Stub implementation of the document generation worker. Placeholder for future CV tailoring and cover letter generation. Returns `status="not_implemented"` for all requests.
- **Location**: `backend/src/applypilot/workers/documents/`
- **Language**: Python
- **Purpose**: Reserve the executor contract slot for document generation while M1 is in stub-only mode.

---

## Code Elements

### worker.py

**Location:** `backend/src/applypilot/workers/documents/worker.py`

#### `DocumentWorker`

Implements the executor contract.

#### `DocumentWorker.run(request: ExecutorRequest) -> ExecutorResult`

Stub — returns immediately with:
- `status = "not_implemented"`
- `details = {"worker": "documents", "mode": request.mode}`

---

## Dependencies

### Internal
- `applypilot.domain.executor.contracts.ExecutorRequest, ExecutorResult`

### External
None (LLM integration not yet wired).

### Dependents
None in M1 — StubExecutor used in place of real workers.

---

## Relationships

```mermaid
graph LR
    contracts["domain/executor/contracts.py"] --> docs["workers/documents/worker.py
DocumentWorker"]
    docs -.->|"future"| llm["LLM API (CV/cover letter generation)"]
```
