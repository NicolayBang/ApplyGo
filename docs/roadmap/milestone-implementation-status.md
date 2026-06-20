# Milestone Implementation Status

**Status:** roadmap clarification  
**Issue:** M6-APP-001  
**Scope:** architecture milestone ladder, implemented state, remaining gaps, and recommended order

This document reconciles the milestone ladder in
`docs/architecture/OpenClaw_Final_Agreed_Architecture.pdf` with the repository as it exists now.
It is a roadmap aid, not implementation approval.

Authority still flows through:

1. `docs/architecture/OpenClaw_Final_Agreed_Architecture.pdf`
2. approved ADRs in `docs/decisions/`
3. `docs/architecture/`
4. `docs/contracts/`
5. `AGENTS.md`

## Status Vocabulary

- **Implemented:** the behavior exists in code, migrations, tests, or committed docs for the current
  baseline.
- **Partial:** part of the milestone outcome exists, but meaningful milestone work remains.
- **Deferred:** intentionally not part of the current milestone closeout.
- **Not implemented:** no committed product behavior exists yet.
- **Blocked by decision:** work needs an ADR, contract, implementation plan, or human approval before
  code begins.

## Milestone Status Table

| Milestone | Architecture Outcome | Implemented Now | Not Done / Remaining Gap | Authority / Reference | Decision Needed | Recommended Next Action |
|---|---|---|---|---|---|---|
| **M1 - Control Plane Foundation** | Data model, tracker, state machine, event log, policy modes. | Implemented. The backend persists jobs, applications, policy decisions, executor actions, and events; state changes pass through the state machine; PostgreSQL migrations and the schema contract define the implemented baseline. | No major M1 product gap is open. Continue maintaining regression coverage and documentation accuracy. | `docs/architecture/locked-plan.md`; `docs/contracts/database-schema-contract.md`; `docs/contracts/event-log-contract.md`; `docs/architecture/current-data-model.md`; `docs/codebase/c4-code-domain-state-machine.md`. | None for closeout. | Treat M1 as implemented baseline; do not reopen unless drift or regression appears. |
| **M2 - Executor Foundation** | Shared executor interface with execute and dry_run support. | Implemented for the safe foundation. The executor contract, dry-run stub, policy-before-executor gate, idempotency key, persisted executor action, and audit evidence exist. | Real outbound worker execution, retry, backoff, rate limits, and scheduler behavior are not implemented. Those are later safety work, not required for M2 closeout. | `docs/contracts/executor-contract.md`; `docs/contracts/policy-contract.md`; `docs/decisions/ADR-0003-m1-database-value-checks.md`; `docs/architecture/database-implementation-roadmap.md`; `docs/codebase/c4-code-domain-executor.md`. | (needs executor hardening contract and implementation plan before retry/rate-limit schema or behavior). | Keep M2 closed for dry-run foundation; defer real execution hardening until after packet/dashboard closeout and explicit safety planning. |
| **M3 - Manual Intake MVP** | Paste job, normalize record, dedupe, save to tracker. | Implemented. Manual intake creates normalized job/application records, deterministic intake enrichment exists, and the M3 company identity baseline now uses `companies`, required `jobs.company_id`, and `jobs.company_source_text` provenance. | Company merge UI, fuzzy matching, AI matching, contact ownership, and external enrichment are not implemented. These are future company expansion or recruiter-communication work, not needed for basic manual intake. | `docs/contracts/m3-company-migration-contract.md`; `docs/decisions/ADR-0005-m3-company-identity.md`; `docs/architecture/current-data-model.md`; `docs/contracts/database-schema-contract.md`; `docs/codebase/c4-code-domain-applications.md`. | (needs company merge/enrichment contract before fuzzy matching, AI matching, external enrichment, or merge UI). | Treat M3 baseline as implemented; keep merge/enrichment as deferred future work. |
| **M4 - Scoring MVP** | Parse job, score fit, explain recommendation, skip reasons. | Implemented for deterministic scoring. Applications can be scored with fit score, confidence, recommendation, reasons, risks, missing data, and red flags; policy context can be derived from stored scoring evidence. | LLM-assisted scoring, richer extraction, and adaptive scoring are not implemented. Current happy path does not require LLM calls. | `docs/roadmap/next-implementation-plan.md`; `docs/contracts/http-api-contract.md`; `docs/codebase/c4-code-domain-applications.md`; `backend/src/applypilot/domain/applications/scoring.py`. | (needs scoring/LLM use contract before LLM-assisted scoring changes). | Mark M4 as implemented baseline; maintain tests and avoid adding LLM dependency to the happy path without approval. |
| **M5 - Packet MVP** | Draft CV bullets, cover note, screening answers, store packet. | Partial and contract-gated. The dashboard can preview packet material from existing evidence, prepare deterministic cover-note/packet text, copy/download reviewer material, persist packet review decisions, expose latest packet review, and append `application_packet.reviewed` audit evidence. | Durable versioned packet storage is not complete. `documents`, `document_versions`, `application_documents`, `answer_library`, and `application_answers` are not implemented as the richer M5 model. Full packet text is not stored by default as an immutable versioned artifact. A **Proposed / Not Implemented** M5 contract now defines this shape and awaits Nicolay + Francis approval before any migration. | `docs/contracts/m5-packet-document-answer-contract.md` (Proposed / Not Implemented); `docs/contracts/m2-application-packet-contract.md`; `docs/contracts/m2-packet-persistence-contract.md`; `docs/decisions/ADR-0002-canonical-data-model.md`; `docs/architecture/database-implementation-roadmap.md`; `docs/roadmap/m2-scope-and-acceptance.md`; `docs/codebase/c4-code-frontend.md`. | (M5 packet/document/answer contract drafted as Proposed; explicit human approval is the gate before schema work). | Approve or revise the proposed M5 contract first; only after approval begin the additive schema, read-model API, and compatibility-cleanup PR sequence. |
| **M6 - Review Dashboard** | Review queue, state transitions, audit visibility, overrides. | Mostly implemented. The React dashboard exposes manual intake, recent applications, review summary, workflow actions, audit timeline, packet review controls, and in-flight action protection. The HTTP API contract records the backend/frontend boundary. | Remaining work is closeout and readiness polish: confirm review-queue behavior, policy/override wording, dashboard regression coverage, and capstone/demo docs. Do not imply external submission or autonomous approvals. | `docs/contracts/http-api-contract.md`; `docs/capstone/dashboard-demo-flow.md`; `docs/capstone/final-manual-validation-checklist.md`; `docs/capstone/reviewer-quickstart.md`; `docs/codebase/c4-code-frontend.md`; `docs/codebase/c4-code-backend-api.md`. | (needs M6 closeout plan before claiming full review-dashboard completion). | Prioritize M5/M6 closeout after this roadmap doc: close packet/dashboard gaps with docs and tests before future external automation. |
| **M7 - Recruiter Email MVP** | Classify emails, update tracker, draft replies through policy gate. | Not implemented. Email worker modules exist only as placeholders behind the executor boundary. No Gmail sync, recruiter contacts, thread/message model, inbound classification, or outbound send path exists. | Contacts, threads, messages, thread-application links, Gmail synchronization, draft reply persistence, idempotency boundaries, and policy-gated send behavior are missing. | `docs/decisions/ADR-0002-canonical-data-model.md`; `docs/architecture/database-implementation-roadmap.md`; `docs/capstone/phase-2-ideas.md`; `docs/codebase/c4-code-workers-email.md`; `docs/contracts/policy-contract.md`; `docs/contracts/executor-contract.md`. | (needs M7 recruiter communication contract, policy/executor plan, Gmail boundary). | Defer until M5/M6 closeout and an approved M7 contract exist. |
| **M8 - Browser Worker MVP** | Fill forms and upload CV; pause or dry-run before submit. | Not implemented. Browser worker modules exist only as placeholders behind the executor boundary. | Playwright/browser automation, form-fill planning, upload behavior, dry-run previews, pause-before-submit controls, security isolation, and kill-switch behavior are missing. | `docs/decisions/ADR-0006-extension-via-modules-not-microservices.md`; `docs/capstone/phase-2-ideas.md`; `docs/codebase/c4-code-workers-browser.md`; `docs/contracts/executor-contract.md`; `docs/contracts/policy-contract.md`. | (needs browser worker ADR/contract, kill switch, dry-run/security plan). | Defer until M7/M8 contracts and high-risk human approval are in place. |
| **M9 - Full-Auto Narrow Mode** | Allowlists, rate limits, kill switch, fallback to semi-auto. | Not implemented. The system has policy modes and dry-run semantics, but no full-auto execution path. | Allowlists, rate limits, kill switch, retry/backoff, executor attempt persistence, production safety controls, and fallback automation rules are missing. | `docs/architecture/OpenClaw_Final_Agreed_Architecture.pdf`; `docs/decisions/ADR-0002-canonical-data-model.md`; `docs/architecture/database-implementation-roadmap.md`; `docs/decisions/ADR-0006-extension-via-modules-not-microservices.md`; `AGENTS.md`. | (needs allowlist/rate-limit/kill-switch/executor hardening contracts and human approval). | Block until M7/M8 are safe, executor hardening is approved, and humans explicitly authorize narrow full-auto work. |

## Cross-Cutting Notes

- `#197` tracks the deferred technical namespace rename from `applypilot` to `applygo`. It is a
  cleanup lane, not milestone closeout work, and should not be bundled into M5/M6 roadmap PRs.
- ADR-0002 uses "Phase 4" for later executor retry/rate-limit hardening. That is not the same as
  architecture milestone M4, which is the scoring MVP.
- Roadmap wording must distinguish implemented behavior from future-state architecture. Planned
  Gmail, browser, full-auto, LLM-dependent, and production behavior must remain explicitly labeled
  as not implemented until code, tests, docs, and approvals exist.

## Recommended Updated Roadmap

1. **M1-M4 implemented baseline:** treat control plane, dry-run executor foundation, manual intake,
   and deterministic scoring as implemented. Maintain regression coverage and docs accuracy.
2. **M5/M6 closeout:** next practical work. Confirm packet/dashboard gaps, strengthen reviewer
   readiness, and avoid schema changes unless an approved contract requires them.
3. **M5 contract-first schema planning:** define versioned documents, reusable answers, retention,
   audit evidence, and API compatibility before any migration.
4. **M7 contract planning:** define recruiter contacts, threads, messages, Gmail sync boundaries,
   policy gates, and idempotency before implementation.
5. **M8/M9 safety contracts:** browser and full-auto work require policy, executor, audit, dry-run,
   kill switch, rate-limit, and human merge-gate approval.
6. **Namespace rename:** keep `#197` separate from roadmap milestone closeout work unless humans
   explicitly prioritize the cleanup lane.
