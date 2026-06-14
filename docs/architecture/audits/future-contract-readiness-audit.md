# Future Contract Readiness Audit

**Status:** Review snapshot

**Date:** 2026-06-14

**Baseline:** `main` at `307359d`

**Scope:** Architecture authority, repository working law, ADRs, contracts, roadmap, diagrams, and
implemented M1 boundaries. This audit proposes no runtime, schema, migration, queue, or worker
change.

## Sources Reviewed

- `docs/architecture/OpenClaw_Final_Agreed_Architecture.pdf`
- `AGENTS.md`
- approved and proposed ADRs under `docs/decisions/`
- current contracts under `docs/contracts/`
- architecture, capstone, diagram, team, and codebase documentation
- implemented state machine, policy, executor, tracker, API, persistence, and tests

## Executive Finding

The implemented M1 spine remains aligned with the governing principles: workflow owns state,
PostgreSQL owns truth, policy owns permission, execution is audited, and dry-run has no external
side effects.

The main future risk is not missing code. It is missing decision artifacts between the architecture
PDF and later implementation. The repository names most later capabilities, but several lack a
contract that defines ownership, evidence, failure behavior, compatibility, and an implementation
gate.

## Immediate Governance Gaps

### 1. Lifecycle reconciliation

The architecture PDF shows:

```text
discovered -> parsed -> scored -> packet_ready/review_needed
-> form_filled -> applied -> interview/rejected/archived
```

The implemented M1 state machine uses:

```text
ApplicationCreated -> Draft -> ReadyForReview -> Approved
-> Submitted -> Archived
```

with rejection branches. The M1 model is valid implemented behavior, but no ADR explains how it
evolves toward the PDF without forcing packet, submission, and conversation concerns into one enum.
Proposed ADR-0006 and the lifecycle transition contract address this gap without authorizing a
migration.

### 2. Architecture supersession ambiguity

The authority hierarchy places the PDF above ADRs, while the drift rule says a conflict may be
superseded by an approved ADR. A dedicated governance ADR must decide whether the PDF is immutable
or may be superseded by explicit human approval. Until then, agents must stop on a PDF conflict.

### 3. Missing contract index

Contracts previously had no central status, owner, prerequisite, or implementation-gate index.
`docs/contracts/README.md` now provides that registry.

### 4. Diagram status drift

The previous component diagram showed Redis dispatching email, browser, and document workers without
marking that path future. Redis exists in Compose, but queue delivery and real worker execution are
not implemented. The diagram is split into implemented M1 and future architecture views.

### 5. Stale database roadmap wording

M1 audit retention is implemented by ADR-0004 and migration `0007`, but the readiness register still
called it next for M1. The roadmap now distinguishes completed M1 retention from future privacy and
retention decisions.

## Missing Contract Program

| Priority | Contract | Why it is required |
|---|---|---|
| 1 | Architecture supersession ADR | Prevent silent drift and contradictory authority claims |
| 2 | Lifecycle and transition model | Reconcile M1 truth with the PDF before new states or substates |
| 3 | Executor hardening | Define action schemas, policy linkage, attempts, retries, timeouts, queues, and idempotency |
| 4 | Human approval and override | Turn `required_overrides` strings into auditable governed actions |
| 5 | M3 intake identity/deduplication | Prevent duplicate jobs and define provenance/re-ingestion behavior |
| 6 | M4 scoring and LLM evidence | Version inputs and explanations; keep LLM output outside permission/state authority |
| 7 | M5 packet/answer | Define immutable versions, reuse, sensitivity, approval, and retention |
| 8 | M6 review workflow | Define queue ownership, actor identity, approvals, overrides, and transition evidence |
| 9 | M7 communication | Define contacts, threads, messages, provider synchronization, privacy, and send boundaries |
| 10 | M8 browser execution | Define supported actions, dry-run evidence, pause/fallback, and failure taxonomy |
| 11 | M9 full-auto controls | Define allowlists, caps, rate limits, kill switch, monitoring, and fallback |

## Staged Delivery

### Near-term, implementation-ready after approval

- architecture supersession ADR;
- lifecycle and transition ADR/contract;
- executor hardening contract;
- human approval and override contract;
- M3 intake identity/deduplication contract;
- M4 scoring and LLM evidence contract.

### Bounded until the owning milestone

- M5 packet and answer model;
- M6 review queue and override UI/API;
- M7 recruiter communication;
- M8 browser execution;
- M9 full-auto controls.

For these later milestones, the registry records purpose, prerequisites, and implementation gates.
Exact schemas and wire formats should be approved immediately before implementation, when the
required product behavior is known.

## Required PR Sequence

1. Audit, registry, and proposed lifecycle foundation.
2. Governance ADR for PDF/ADR supersession.
3. M2 executor hardening and human override contracts.
4. M3 intake identity/deduplication contract.
5. M4 scoring and LLM evidence contract.
6. Per-milestone M5-M9 decision and contract PRs.
7. Separate implementation PRs only after the owning contracts are approved.

Contract/ADR PRs must remain separate from migrations and backend implementation. Changes to
architecture authority, contracts, or `AGENTS.md` require CI and explicit Nicolay and Francis
approval; they are not eligible for low-risk documentation auto-merge.
