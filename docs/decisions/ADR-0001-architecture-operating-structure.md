# ADR-0001-architecture-operating-structure

## Status
Approved

## Date
2026-06-11

## Context
ApplyPilot requires a locked architecture baseline and a consistent operating structure before business logic implementation. The team aligned on the final OpenClaw architecture and a repository governance model that enforces contract-first development, dry-run safety, and architecture drift detection.

## Decision
Adopt the following architecture authority order for all implementation and review decisions:

1. `docs/architecture/OpenClaw_Final_Agreed_Architecture.pdf`
2. Approved ADRs in `docs/decisions/`
3. `docs/architecture/`
4. `docs/contracts/`
5. `AGENTS.md`
6. Chat discussion

Establish repository operating structure and naming conventions as defined in `AGENTS.md`, with documentation and contract scaffolding under `docs/`.

Any code conflict with `docs/architecture/OpenClaw_Final_Agreed_Architecture.pdf` is architecture drift unless superseded by a newer approved ADR.

## Consequences
- Architecture discussions shift from chat-first to artifact-first.
- Implementation changes that affect architecture must be represented by ADRs.
- Review and CI checks can enforce document and naming conventions deterministically.
- Business logic remains out of scope for Milestone 1 until control-plane spine artifacts are complete.

## Supersedes
None.

## Superseded by
None.
