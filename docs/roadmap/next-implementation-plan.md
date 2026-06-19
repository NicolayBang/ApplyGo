# Next Implementation Plan

**Status:** implementation governance plan
**Issue:** M3-APP-002
**Scope:** lean roadmap, workflow laws, and readiness queue

This plan keeps the next implementation wave explicit without creating a large documentation
program. The GitHub issue is the working ledger. This file records only the durable repo-facing
facts that future contributors need before opening scoped PRs.

## Current Baseline

Implemented now:

- **M1 workflow spine:** manual intake, state machine, scoring, policy decisions, dry-run executor
  evidence, and audit visibility.
- **M2 packet review persistence:** packet review decisions are persisted, audit evidence is
  appended, and the dashboard can record approve, reject, and changes-requested decisions.
- **M3 company identity baseline:** `companies` owns canonical company identity, `jobs.company_id`
  is required, and `jobs.company_source_text` preserves raw intake provenance.

Not implemented:

- Gmail, browser, or real submission side effects.
- LLM-required happy paths.
- Production deployment.
- Auth or user account model.
- Lifecycle substates beyond the current application state.
- Executor retry, backoff, or rate-limit semantics.
- M5 reusable document, document-version, or answer-library model.
- M7 recruiter contacts, threads, messages, or Gmail sync.
- Company merge UI, fuzzy matching, AI matching, or external enrichment.

## Workflow Laws

Apply these laws before opening implementation PRs:

- **Authority order:** architecture PDF, approved ADRs, `docs/architecture/`, `docs/contracts/`,
  `AGENTS.md`, then chat discussion.
- **Policy before executor:** record a policy decision before dry-run or execution.
- **Audit before state update:** record execution result evidence before advancing workflow state.
- **Side-effect gate:** no external side effect without explicit approval, dry-run-first design, and
  audit evidence.
- **High-risk merge gate:** schema, state machine, event log, policy, executor, contracts, ADRs,
  CI, security, and `AGENTS.md` changes require human merge review.
- **One-issue, multi-PR discipline:** use issue M3-APP-002 as the ledger; keep each PR scoped to one
  concern.

## Planned PRs

1. **Roadmap reconciliation:** add this plan and update the roadmap index.
2. **HTTP API contract:** document the current backend/frontend HTTP boundary only if the contract
   is still missing after inspection.
3. **Frontend in-flight protection:** disable relevant dashboard action buttons while requests are
   running so duplicate workflow and audit records are harder to create.

PRs should use `Part of #213` until the final planned PR. Only the final PR should use
`Closes #213`, after the earlier PRs have merged.

## Documentation Budget

For M3-APP-002:

- Maximum new docs: two.
- Maximum existing docs edited: three.
- No root `SESSIONS.md`.
- No new ADR unless implementation discovers an architecture decision that cannot be handled by
  existing authority.
- Keep working-session details in the GitHub issue when they do not need committed repository docs.
