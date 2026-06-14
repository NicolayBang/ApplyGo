# Capstone Process Scaffold

## Objective
Deliver the platform spine with architecture alignment, deterministic M1 workflow behavior, and
auditable execution flow before any external automation.

## Milestone 1 Deliverables
- Canonical tracker entities and persistence scaffolding
- State machine definition and transition guard scaffolding
- Append-only event log contract and minimal persistence path
- Policy contract and mode evaluation scaffolding
- Executor contract with dry-run/execute parity and stub behavior
- Minimal dashboard views for tracker and audit timeline
- PostgreSQL migration and validation workflow
- Reviewer-facing demo runbook and MVP status summary

## Definition of Done
- Create an application record
- Transition through defined states
- Log each policy and execution event in order
- Evaluate a policy decision across modes
- Simulate executor action in dry-run
- View tracker state and timeline in dashboard

## Process Rules
- Architecture-first: honor authority order before implementation.
- Drift control: any conflict against locked PDF is architecture drift unless superseded by approved ADR.
- No external side effects in this phase.
- Keep deterministic M1 behavior separate from future LLM, Gmail, browser, and production automation.

## Working Agreement
- Prefer small PRs aligned to one contract/domain at a time.
- Include contract/doc updates with each structural code change.
- Capture architecture-affecting decisions as ADRs before merge.
