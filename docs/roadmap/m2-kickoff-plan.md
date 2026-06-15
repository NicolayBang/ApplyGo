# M2 Kickoff Plan

**Status:** proposed planning baseline
**Date:** 2026-06-15
**Audience:** Nicolay, Francis, contributors, and review agents

M1 is now the MVP-ready capstone baseline. M2 should build on that baseline without destabilizing
the validated demo path.

## M2 Goal

Move ApplyPilot from a governed workflow spine to a useful application packet workflow.

In plain terms, M2 should help a human prepare better application material while preserving the
M1 rules:

- workflow owns state;
- database owns truth;
- policy owns permission;
- executor behavior remains dry-run or human-approved;
- audit evidence stays visible.

## Recommended M2 Theme

**Application packet preparation and review.**

This is the safest next step because it creates user value without introducing real external
submission, Gmail side effects, browser automation, or production hosting risk.

M2 should focus on:

- clearer application packet data;
- human-reviewed cover note or answer draft artifacts;
- dashboard review of prepared material;
- audit events for packet preparation decisions;
- exportable or copyable review output if useful.

## First PR Sequence

1. **M2 scope and acceptance criteria**
   - Define the exact M2 demo path.
   - Confirm what counts as M2 done.
   - Keep M1 demo behavior stable.

2. **Packet/domain contract review**
   - Review current `documents` placeholder behavior.
   - Decide whether M2 needs a lightweight packet contract before implementation.
   - Do not start a migration until the contract is clear.

3. **Dashboard packet review design**
   - Add a reviewer-facing packet section or wireframe.
   - Keep it backed by current data or clearly label it as proposed before implementation.

4. **Deterministic draft artifact proof**
   - Add a small deterministic cover-note or application-summary draft generator.
   - Keep it human-reviewed and non-external.
   - Log generation or review events if persisted.

5. **Validation and demo update**
   - Extend the demo script/checklist only after implemented behavior exists.
   - Keep frontend/backend checks green.

## Explicitly Deferred

M2 should not start with:

- ADR-0005 company identity migration unless Nicolay and Francis reopen timing;
- real Gmail sending;
- browser automation;
- real application submission;
- production deployment;
- LLM-dependent drafting as a required path;
- microservices or distributed worker infrastructure.

These may become later milestone work, but they are not the safest first move after M1.

## ADR-0005 Timing

ADR-0005 remains approved direction, not immediate implementation approval.

Revisit ADR-0005 when one of these becomes true:

- packet work needs reliable company identity beyond `jobs.company`;
- duplicate companies are causing real workflow or dashboard confusion;
- a new schema migration is already justified by M2/M3 scope;
- Nicolay and Francis explicitly approve moving the company migration forward.

Until then, preserve the current M1-compatible `jobs.company` behavior.

## Validation Expectations

Any M2 PR that changes application code should include appropriate validation:

- frontend syntax check when `frontend/` changes;
- backend lint and pytest when backend behavior changes;
- PostgreSQL migration validation when schema changes;
- manual dashboard validation when reviewer flow changes.

Any PR touching state machine, DB schema, event log, policy, executor, or contracts must include
runnable tests or explain why tests are deferred.

## Human Review Gates

Require Nicolay and Francis review before:

- adding or changing database tables;
- implementing ADR-0005;
- changing policy permission behavior;
- adding an executor side effect;
- introducing Gmail, browser, or LLM-dependent behavior;
- changing M1 demo acceptance criteria.

## M2 Success Criteria

M2 is successful when ApplyPilot can demonstrate a human-controlled application packet workflow
that:

- starts from an existing application;
- prepares useful review material;
- makes the next human action clear;
- records material decisions in the audit trail when persisted;
- does not perform external submission;
- does not weaken M1 policy, dry-run, or audit guarantees.
