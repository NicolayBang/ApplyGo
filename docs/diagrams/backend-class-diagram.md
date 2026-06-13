# Backend Class Diagram

Status: living implementation reference.

This diagram describes the current backend class and module shape. It is not an architecture authority. If this diagram conflicts with the locked architecture PDF, approved ADRs, contracts, or implemented behavior, those sources win and this diagram should be updated.

## Current Backend Shape

```mermaid
classDiagram
    direction LR

    class Job {
        +UUID id
        +str source_url
        +str title
        +str company
        +str location
        +bool remote_ok
        +str job_type
        +str ats_type
        +str salary_raw
        +datetime created_at
        +datetime updated_at
    }

    class Application {
        +UUID id
        +UUID job_id
        +str state
        +str automation_mode
        +int fit_score
        +str confidence
        +str recommendation
        +list score_reasons
        +list score_risks
        +list missing_data
        +list red_flags
        +datetime created_at
        +datetime updated_at
    }

    class Document {
        +UUID id
        +UUID application_id
        +str doc_type
        +str content
        +dict content_json
        +int version
        +datetime created_at
    }

    class EmailThread {
        +UUID id
        +UUID application_id
        +str external_thread_id
        +str subject
        +str direction
        +str classification
        +str raw_body
        +str draft_reply
        +datetime sent_at
        +datetime created_at
    }

    class PolicyDecision {
        +UUID id
        +UUID application_id
        +str action_type
        +str mode
        +bool allowed
        +list reasons
        +list risks
        +datetime created_at
    }

    class ExecutorAction {
        +UUID id
        +UUID application_id
        +str idempotency_key
        +str action_type
        +str execution_mode
        +str status
        +dict payload
        +dict result
        +datetime created_at
        +datetime completed_at
    }

    class EventLogEntry {
        +UUID id
        +UUID application_id
        +str event_type
        +str actor
        +str from_state
        +str to_state
        +dict payload
        +datetime created_at
    }

    class Tracker {
        -Session _session
        -ApplicationStateMachine _state_machine
        +create_job(JobCreate) Job
        +get_job(UUID) Job
        +create_application(ApplicationCreate) Application
        +get_application(UUID) Application
        +list_applications(str, int, int) list~Application~
        +update_state(UUID, str, str, dict) Application
        -_append_event(...) EventLogEntry
        +get_events(UUID) list~EventLogEntry~
    }

    class ApplicationState {
        <<enumeration>>
        APPLICATION_CREATED
        DRAFT
        READY_FOR_REVIEW
        APPROVED
        SUBMITTED
        REJECTED
        ARCHIVED
    }

    class ApplicationStateMachine {
        +can_transition(ApplicationState, ApplicationState) bool
        +next_states(ApplicationState) set~ApplicationState~
        +apply_transition(ApplicationState, ApplicationState) ApplicationState
    }

    class InvalidStateTransitionError {
        <<exception>>
    }

    class ExecutorRequest {
        +str action_type
        +ExecutionMode mode
        +str application_id
        +str idempotency_key
        +dict payload
    }

    class ExecutorResult {
        +str status
        +dict details
    }

    class ExecutionMode {
        <<enumeration>>
        EXECUTE
        DRY_RUN
    }

    class EmailWorker {
        +run() None
    }

    class BrowserWorker {
        +run() None
    }

    class DocumentWorker {
        +run() None
    }

    Job "1" --> "*" Application : applications
    Application "1" --> "*" Document : documents
    Application "1" --> "*" EmailThread : email_threads
    Application "1" --> "*" PolicyDecision : policy_decisions
    Application "1" --> "*" ExecutorAction : executor_actions
    Application "1" --> "*" EventLogEntry : events

    Tracker --> Job : creates/reads
    Tracker --> Application : creates/updates
    Tracker --> EventLogEntry : appends
    Tracker --> ApplicationStateMachine : validates transitions
    ApplicationStateMachine --> ApplicationState : uses
    ApplicationStateMachine ..> InvalidStateTransitionError : raises

    ExecutorRequest --> ExecutionMode : uses
    ExecutorAction --> ExecutorRequest : persists requested action
    ExecutorAction --> ExecutorResult : stores result payload

    EmailWorker ..> ExecutorRequest : future contract
    BrowserWorker ..> ExecutorRequest : future contract
    DocumentWorker ..> ExecutorRequest : future contract
```

## Notes

- The ORM model is centered on `Application` as the canonical hub record.
- `Tracker` is the current repository boundary for creating jobs, creating applications, listing applications, updating state, and appending event log entries.
- `ApplicationStateMachine` owns transition validation. Invalid transitions raise `InvalidStateTransitionError`.
- `ExecutorRequest`, `ExecutorResult`, and `ExecutionMode` define the current executor contract shape, while worker implementations remain stubs in M1.
- This diagram should be refreshed when backend classes, relationships, or major methods change.
