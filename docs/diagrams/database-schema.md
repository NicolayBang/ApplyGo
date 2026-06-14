# Database Schema Views

These diagrams intentionally separate implemented M1 behavior from proposed future design.
Diagrams are explanatory artifacts; models, migrations, contracts, and approved ADRs remain higher
authority.

## Current M1 Schema

**Status: Implemented**

```mermaid
erDiagram
    JOBS ||--o{ APPLICATIONS : has
    APPLICATIONS ||--o{ DOCUMENTS : owns
    APPLICATIONS ||--o{ EMAIL_THREADS : owns
    APPLICATIONS ||--o{ POLICY_DECISIONS : records
    APPLICATIONS ||--o{ EXECUTOR_ACTIONS : records
    APPLICATIONS ||--o{ EVENT_LOG : audits

    JOBS {
        uuid id PK
        varchar company
        varchar title
        text raw_text
        boolean remote_ok
    }
    APPLICATIONS {
        uuid id PK
        uuid job_id FK
        varchar state
        varchar automation_mode
        integer fit_score
        varchar confidence
        varchar recommendation
    }
    DOCUMENTS {
        uuid id PK
        uuid application_id FK
        varchar doc_type
        integer version
    }
    EMAIL_THREADS {
        uuid id PK
        uuid application_id FK
        varchar direction
        varchar classification
    }
    POLICY_DECISIONS {
        uuid id PK
        uuid application_id FK
        varchar action_type
        varchar mode
        varchar decision
        boolean allowed
    }
    EXECUTOR_ACTIONS {
        uuid id PK
        uuid request_id UK
        uuid application_id FK
        varchar worker
        varchar idempotency_key UK
        varchar execution_mode
        varchar status
        varchar requested_by
    }
    EVENT_LOG {
        uuid id PK
        uuid application_id FK
        varchar event_type
        varchar actor
        varchar from_state
        varchar to_state
    }
```

See `docs/contracts/database-schema-contract.md` for complete column and constraint details.

## Future Data Model

**Status: Planned / Not Implemented**

This view records the proposed normalization direction in ADR-0002. It is not a description of the
current database and does not authorize migrations.

```mermaid
erDiagram
    COMPANIES ||--o{ JOBS : posts
    COMPANIES ||--o{ CONTACTS : employs
    JOBS ||--o{ APPLICATIONS : pursued_by

    DOCUMENTS ||--o{ DOCUMENT_VERSIONS : versions
    APPLICATIONS ||--o{ APPLICATION_DOCUMENTS : attaches
    DOCUMENT_VERSIONS ||--o{ APPLICATION_DOCUMENTS : used_as

    CONTACTS ||--o{ THREADS : primary_contact
    THREADS ||--o{ MESSAGES : contains
    APPLICATIONS ||--o{ THREAD_APPLICATIONS : relates
    THREADS ||--o{ THREAD_APPLICATIONS : relates

    ANSWER_LIBRARY ||--o{ APPLICATION_ANSWERS : sources
    APPLICATIONS ||--o{ APPLICATION_ANSWERS : uses

    APPLICATIONS ||--o{ APPLICATION_EVENTS : audits
    APPLICATIONS ||--o{ POLICY_DECISIONS : gates
    APPLICATIONS ||--o{ EXECUTOR_RUNS : executes

    COMPANIES {
        uuid id PK
        varchar name
        varchar domain
    }
    APPLICATION_DOCUMENTS {
        uuid application_id PK,FK
        uuid document_version_id PK,FK
        varchar role
    }
    THREAD_APPLICATIONS {
        uuid thread_id PK,FK
        uuid application_id PK,FK
    }
```

## Phase Boundary

- M1 keeps the current seven-table aggregate.
- M3 may normalize companies.
- M5 may introduce packet/document version and answer entities.
- M7 may introduce contacts, messages, and many-to-many recruiter threads.
- Executor retry/backoff and table naming changes require a separately approved migration.
