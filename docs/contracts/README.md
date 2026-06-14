# Contract Registry

**Status:** Governance index

**Last reviewed:** 2026-06-14

This registry tracks the contracts required to move ApplyPilot from the implemented M1 spine
through later milestones. It is an index, not an implementation authorization.

## Status Vocabulary

- **Implemented:** represented by current code, tests, and persistence behavior.
- **Approved:** approved direction, possibly with a separate implementation-timing gate.
- **Proposed:** ready for human architecture review but not binding.
- **Missing:** required before the owning capability may be implemented.
- **Blocked:** cannot be completed until a named prerequisite or human decision is resolved.

## Registry

| Contract area | Status | Milestone | Owner | Prerequisites | Implementation gate |
|---|---|---|---|---|---|
| M1 database schema | Implemented | M1 | Backend | None | Models, migrations, and PostgreSQL tests stay aligned |
| M1 event log | Implemented | M1 | Workflow | None | Append-only ordering and vocabulary tests remain green |
| M1 policy evaluation | Implemented | M1 | Policy | None | Policy decision is persisted before executor dispatch |
| M1 executor request/result | Implemented | M1/M2 foundation | Executor | Policy decision | Dry-run remains side-effect free; execute remains unimplemented |
| M3 company migration | Approved | M3 | Data model | ADR-0005; 3NF amendment approval | Nicolay and Francis approve timing; PostgreSQL compatibility evidence passes |
| Future canonical data model | Proposed | M3/M5/M7 | Architecture | ADR-0002 approval | Each milestone receives its own schema and migration contract |
| Lifecycle and transition model | Proposed | M2+ | Workflow | ADR-0006 review | Human approval plus migration and API compatibility contracts |
| Architecture supersession rule | Missing | Governance | Architecture governance | Human interpretation of PDF/ADR precedence | Dedicated approved ADR |
| Executor hardening and queue delivery | Missing | M2/later | Executor/DevOps | Lifecycle evidence rules; human override contract | Action schemas, attempts, retry, timeout, idempotency, and delivery tests |
| Human approval and override | Missing | M2/M6 | Policy/Workflow | Actor identity and audit vocabulary | Overrides are persisted, scoped, expiring where needed, and never rewrite decisions |
| Job identity and ingestion deduplication | Missing | M3 | Intake/Data model | Company timing decision | Canonical URL, provenance, duplicate, and re-ingestion behavior approved |
| Scoring and LLM evidence | Missing | M4 | Scoring/AI | Job identity contract | Versioned inputs, provenance, validation, thresholds, and deterministic fallback |
| Packet, document, and answer model | Missing | M5 | Documents/Data model | Lifecycle contract; retention policy | M5 schema, versioning, sensitivity, and migration contract approved |
| Review queue and override workflow | Missing | M6 | Workflow/UI | Human override contract; lifecycle contract | API/UI transitions use persisted evidence and auditable actor identity |
| Recruiter communication | Missing | M7 | Email/Data model | Privacy/retention; executor hardening | Provider sync, idempotency, thread ownership, and draft/send boundaries approved |
| Browser execution | Missing | M8 | Browser/Executor | Executor hardening; full action schemas | Dry-run parity, pause/fallback rules, artifact evidence, and supported-template limits |
| Full-auto guardrails | Missing | M9 | Policy/Operations | M7/M8 evidence; rate limiting; kill switch | Allowlists, caps, fallback, monitoring, and human shutdown path tested |
| Long-term audit privacy and retention | Missing | Before M7/M8 | Governance/Data | Data sensitivity inventory | Retention, redaction, erasure, access, and immutable evidence boundary approved |

## Binding Boundaries

- Implemented contracts describe current M1 behavior.
- Approved contracts may still require an explicit timing gate.
- Proposed, Missing, and Blocked entries do not authorize code, schema, queue, worker, or API changes.
- A contract that changes architecture authority, workflow state, policy permission, executor
  behavior, or schema requires Nicolay and Francis to approve it before implementation.
- Implementation PRs must update this registry when a contract status changes.

## Ordered Contract Program

1. Resolve architecture supersession governance.
2. Approve or revise the lifecycle and transition proposal.
3. Define executor hardening and human override contracts.
4. Define M3 intake identity and deduplication while keeping company timing separately gated.
5. Define M4 scoring and LLM evidence.
6. Define M5 through M9 contracts immediately before their owning milestones.
7. Finalize long-term privacy and retention before recruiter email or browser execution.
