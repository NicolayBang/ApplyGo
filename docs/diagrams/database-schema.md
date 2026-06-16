# Database Schema Views

These diagrams intentionally separate implemented behavior from approved and proposed future design.
Diagrams are explanatory artifacts; models, migrations, contracts, and approved ADRs remain higher
authority.

## Current Implemented Schema

**Status: Implemented**

```mermaid
erDiagram
    COMPANIES ||--o{ JOBS : identifies
    JOBS ||--o{ APPLICATIONS : has
    APPLICATIONS ||--o{ DOCUMENTS : owns
    APPLICATIONS ||--o{ EMAIL_THREADS : owns
    APPLICATIONS ||--o{ APPLICATION_PACKET_REVIEWS : reviews
    APPLICATIONS ||--o{ POLICY_DECISIONS : records
    APPLICATIONS ||--o{ EXECUTOR_ACTIONS : records
    APPLICATIONS ||--o{ EVENT_LOG : audits

    COMPANIES {
        uuid id PK
        varchar name
        varchar normalized_name
        varchar domain
        varchar normalized_domain
    }
    JOBS {
        uuid id PK
        uuid company_id FK
        varchar company_source_text
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
    APPLICATION_PACKET_REVIEWS {
        uuid id PK
        uuid application_id FK
        varchar decision
        varchar reviewed_by
        varchar source
        text packet_text
        text notes
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

This implemented view now includes the M2 `application_packet_reviews` table and the M3 company
identity cutover (`jobs.company_id`, `jobs.company_source_text`, and `companies`).

## Future Data Model

**Status: Later Phases / Not Implemented**

The company portion is already implemented in the current schema. The M5/M7 portions record the
proposed broader normalization direction in ADR-0002. This future view is not a description of the
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
        varchar normalized_name
        varchar domain
        varchar normalized_domain
        timestamptz created_at
        timestamptz updated_at
    }
    JOBS {
        uuid id PK
        uuid company_id FK
        varchar company_source_text
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

- M1 keeps the original application aggregate behavior.
- M2 adds human packet review persistence and `application_packet.reviewed` audit evidence.
- M3 company identity is implemented for the deterministic baseline: `jobs.company_id` is required,
  canonical company facts live on `companies`, and raw employer provenance lives in
  `jobs.company_source_text`.
- M5 may introduce packet/document version and answer entities.
- M7 may introduce contacts, messages, and many-to-many recruiter threads.
- Executor retry/backoff and table naming changes require a separately approved migration.
