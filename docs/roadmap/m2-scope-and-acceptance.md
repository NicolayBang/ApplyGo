# M2 Scope And Acceptance Criteria

**Status:** proposed M2 acceptance baseline
**Date:** 2026-06-15
**Audience:** Nicolay, Francis, contributors, and review agents

This document turns the M2 kickoff plan into a concrete acceptance gate. It is a planning artifact,
not implementation approval.

## M2 Working Name

Application packet preparation and review.

## M2 Problem Statement

M1 proves that ApplyPilot can create, score, policy-check, dry-run, and audit an application. M2
should make that workflow more useful by helping a human prepare and review application material
before any external automation exists.

M2 should answer:

- What would I submit or send?
- Why is this application a good or risky fit?
- What still needs a human decision?
- What evidence has been recorded?

## In Scope

M2 may include:

- a packet/review section in the dashboard;
- deterministic application summary or cover-note draft output;
- copyable/exportable packet text;
- human review status for prepared material;
- audit events when packet decisions are persisted;
- tests for any packet-generation or persistence behavior;
- demo docs that explain the M2 workflow after implementation exists.

## Out Of Scope

M2 must not include by default:

- real application submission;
- Gmail sending;
- browser automation;
- production deployment;
- ADR-0005 company identity migration;
- required LLM calls for the happy path;
- microservices, Kubernetes, or distributed worker infrastructure.

## Proposed M2 Demo Path

The M2 demo should extend M1 like this:

```text
existing application
-> score and policy evidence
-> prepare application packet
-> review packet content
-> record human review decision
-> inspect packet/audit evidence
```

The exact UI can evolve, but the demo should remain human-controlled and side-effect free.

## Acceptance Criteria

M2 is accepted when:

- a reviewer can start from an existing application;
- the dashboard presents a clear application packet or review material section;
- the packet uses existing job/application/scoring evidence;
- the next human action is clear;
- generated or prepared content is deterministic unless explicitly labeled otherwise;
- any persisted packet decision creates audit evidence;
- external side effects remain absent;
- M1 demo behavior still passes;
- frontend/backend checks pass for the changed scope;
- M2 docs describe only implemented behavior after implementation begins.

## Stop Conditions

Pause M2 implementation and review with Nicolay and Francis if:

- a feature requires schema changes before the packet contract is agreed;
- packet work depends on company normalization;
- a feature needs Gmail, browser, or external submission behavior;
- policy permission rules need to change;
- executor side effects are proposed;
- M1 demo behavior breaks or becomes harder to explain.

## First Implementation Candidate

The safest first implementation candidate is a dashboard-only packet preview backed by existing
application data:

- job title, company, location, source URL;
- fit score, confidence, recommendation;
- score reasons, risks, missing data, and red flags;
- latest policy decision;
- latest dry-run executor result when present.

This can prove the M2 review experience before adding new persistence or migrations.

## Validation Plan

For docs-only PRs:

- run `git diff --check`;
- explain why backend/frontend tests were not required.

For frontend-only packet preview PRs:

- run `node --check frontend/app.js`;
- run the relevant dashboard asset contract tests;
- manually inspect the dashboard if layout changes are visible.

For backend or persistence PRs:

- run backend lint and pytest;
- add runnable tests for packet generation, persistence, and audit behavior;
- run PostgreSQL-backed validation if migrations or DB behavior change.

## Decision Required Before Migration

Before any M2 migration, approve a packet contract that defines:

- table ownership, if new tables are needed;
- fields and nullability;
- retention and delete behavior;
- audit event names;
- API compatibility;
- migration and rollback expectations.

Until that contract exists, prefer using the current M1 data to shape the dashboard experience.
