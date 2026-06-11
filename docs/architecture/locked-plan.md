# Locked Plan

## Baseline
This repository follows the final architecture baseline in:

- `docs/architecture/OpenClaw_Final_Agreed_Architecture.pdf`

Status: locked baseline design. Remaining work should focus on implementation artifacts, not reopening core architecture.

## Authority Order
1. `docs/architecture/OpenClaw_Final_Agreed_Architecture.pdf`
2. Approved ADRs in `docs/decisions/`
3. `docs/architecture/`
4. `docs/contracts/`
5. `AGENTS.md`
6. Chat discussion

If code conflicts with the PDF, flag it as architecture drift unless a newer approved ADR explicitly supersedes it.

## Locked Principles
- Workflow owns state.
- Database owns truth.
- Policy owns permission.
- LLM is constrained to extraction/classification/scoring support/drafting.
- Workers execute only approved structured actions.
- Audit before and after execution.
- Dry-run support from day one through the executor contract.

## Milestone Scope
Milestone 1 is platform spine only:

- Canonical tracker and state machine
- Append-only event log
- Policy engine and modes
- Executor contract with execute/dry_run parity
- Stub executor and minimal dashboard visibility

No business logic implementation for Gmail, browser automation, or autonomous LLM action execution in this milestone.
