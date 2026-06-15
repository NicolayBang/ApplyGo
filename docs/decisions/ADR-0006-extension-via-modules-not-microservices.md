# ADR-0006-extension-via-modules-not-microservices

| Field | Value |
|-------|-------|
| **Status** | Proposed |
| **Date** | 2026-06-14 |
| **Owner** | Nicolay (architecture) |
| **Reviewers required** | Nicolay + Francis (High risk — system structure / service boundaries) |
| **Related** | `docs/architecture/OpenClaw_Final_Agreed_Architecture.pdf`; `docs/decisions/ADR-0001-architecture-operating-structure.md`; `docs/decisions/ADR-0002-canonical-data-model.md`; `docs/architecture/locked-plan.md`; `docs/contracts/executor-contract.md`; `docs/contracts/policy-contract.md`; `docs/capstone/phase-2-ideas.md`; `docs/diagrams/component-diagram.md` |

> **Authority order:** architecture PDF → approved ADRs → `docs/architecture/` → `docs/contracts/`
> → `AGENTS.md` → chat. This ADR records *direction* and a *decision rule*. It does **not**
> authorize any migration, new service, LLM integration, or feature. Each candidate below requires
> its own YouTrack ticket, per-milestone contract, and risk-tier sign-off before any code is written.

---

## Status

**Proposed.** Requires Nicolay + Francis sign-off because it sets a binding rule for how the system
is structured and how future work is partitioned.

---

## Context

A team chat discussion raised splitting future features — starting with a resume/CV builder — into
**microservices**, so each contributor could own a "whole software" and plug them together. The
appeal is real: parallel ownership across a small team, and clear personal surface area.

The locked architecture and ADR-0002 already point the other way. ADR-0002's "Explicitly not decided
here" section states the project takes on **no microservices, service-per-aggregate, message bus, or
queue beyond the already-planned Redis**. The OpenClaw baseline is a single governed control plane
where **the database owns truth**. A microservice carries either its own database (which splits the
source of truth and breaks that invariant) or a shared database across services (a recognised
anti-pattern that creates hidden coupling and consistency drift).

The instinct to parallelise is correct; the chosen mechanism is the issue. Parallel ownership in a
small team comes from **clean contracts and module boundaries**, not **network boundaries**. The
locked architecture already provides the seams for this: the LLM layer (extract / classify / score /
draft), the executor contract, the worker pattern, and read-only access to the canonical PostgreSQL
database and append-only event log. The existing repository already reserves worker slots
(`workers/email`, `workers/browser`, `workers/documents`) behind one executor contract — extension
points are present by design.

This ADR records the resolution and gives the team a reusable decision rule, plus a catalogued
parking lot of candidate extensions so the chat ideas are not lost. Several candidates overlap
`docs/capstone/phase-2-ideas.md`; this ADR consolidates the structural decision, not the backlog.

---

## Decision

### 1. Default extension mechanism

New capabilities are delivered as **modules** (backend packages under the existing `backend/` domain
folders) or as **workers behind the shared executor contract**, in the existing monorepo, reading the
single canonical PostgreSQL database. Frontend capabilities are delivered as **UI surfaces** in
`frontend/`. The default is **not** a separate service, **not** a per-feature database, and **not** a
message bus or queue beyond the already-planned Redis.

### 2. Service-split test

A capability is promoted to its own deployable **process** only if at least one of the following holds:

1. **Distinct security surface** — separate credentials, permissions, or attack surface that warrants
   isolation from the control plane.
2. **Independent kill-switch / isolation requirement** — it must be stoppable or sandboxed on its own,
   independently of the rest of the system.
3. **Heavyweight or conflicting runtime dependencies** — e.g. browser automation binaries that should
   not share the API process's runtime.

If none hold, it ships as a module or a worker. Convenience, "feels cleaner," or wanting separate
ownership are **not** on this list — ownership is achieved through module boundaries and contracts.

### 3. The one currently justified split

The **browser worker (M8, Playwright)** passes the test on all three counts and is the single
justified future split. Even then it is a **worker process** that still shares the canonical database
and the executor contract — it is process isolation, not a service-per-aggregate with its own data
store. No other planned capability currently passes the test.

### 4. Candidate extension catalogue (direction only — authorises nothing)

Each candidate maps to an existing seam, a proposed milestone, and a **provisional** risk tier per the
`AGENTS.md` risk table. Tiers are starting estimates for planning, **not** approvals; the real tier is
set at the risk gate when a ticket is opened.

| # | Candidate | Seam | Proposed milestone | Provisional risk | Notes |
|---|-----------|------|--------------------|------------------|-------|
| 1 | Resume / CV tailoring | LLM draft → `documents` worker | M5 | Medium → High | This is packet generation, not a new app. High if it requires the documents worker wiring, the first LLM integration, or M5 packet/answer schema. |
| 2 | Cover letter / recruiter-reply draft | LLM draft → `documents`/`email` worker | M5 / M7 | Medium → High | Drafting only. Any actual send is candidate #10 and is Critical. |
| 3 | Interview-prep generator | LLM draft + new read model + UI | post-M5 | Medium | No external side effects. Validate LLM output before persistence (invariant 8). |
| 4 | Skills-gap analyzer | LLM classify/score | post-M5 | Medium | Advisory only; profile vs. role requirements. |
| 5 | ATS-compatibility checker | Deterministic checks + LLM score | M5-adjacent | Medium | Keyword coverage / formatting vs. job text. |
| 6 | Application funnel analytics | Read `event_log` + tracker → display | post-M1 | Low | Overlaps `phase-2-ideas.md` "aggregate funnel metrics". Read-only; the event log is the natural source. |
| 7 | Cross-board duplicate detection | Extends intake dedupe | M3-adjacent | Low → Medium | Low if pure read; Medium if it touches intake/classification. |
| 8 | Company enrichment | Contained worker, inbound reads | M3+ | Medium | Reads, not side effects, so outside the policy gate — but respect source ToS / rate limits. Salary/legal signals stay advisory only, per the full-auto guardrails. |
| 9 | Follow-up scheduler (draft) | Read tracker + LLM draft | M7-adjacent | Medium | Overlaps `phase-2-ideas.md` "stale application detection". **Proposes** transitions and drafts; never mutates state directly. |
| 10 | Follow-up email send | `email` worker via executor contract | M7 | Critical | Gmail send. Requires policy decision, dry-run first, Nicolay + Francis sign-off, and no self-merge. |

### 5. Invariants every candidate must honour

Regardless of seam, each candidate preserves: workflow owns state; database owns truth; policy owns
permission; the LLM stays fenced to extraction / classification / scoring / drafting and never
autonomously chooses next actions; LLM outputs are validated before persistence or execution; no
external side effect occurs without a logged policy decision; dry-run precedes execution; and the
event log records decisions before and results after. This ADR reopens none of those boundaries — it
is additive.

---

## Consequences

**Positive**

- Parallel ownership is preserved through module/worker/UI boundaries and contracts, without the
  distributed-systems tax (cross-service consistency, network failure handling, deploy orchestration).
- The single source of truth stays intact; "database owns truth" is not weakened.
- The decision is consistent with the locked plan and ADR-0002; nothing already settled is reopened.
- Chat ideas are captured and tiered rather than lost, with overlaps to the existing parking lot made
  explicit.

**Costs / risks**

- Module discipline and clear internal contracts must be maintained so parallel work does not collide;
  this replaces, rather than removes, the coordination need.
- The browser worker split (M8) still owes its own isolation, kill-switch, and security design when its
  milestone opens.
- Provisional risk tiers in the catalogue must be re-confirmed at each risk gate; they are not a
  shortcut around sign-off.

**Constraints (binding)**

- No candidate above is authorised by this ADR. Implementation of any of them requires a YouTrack
  ticket, the relevant per-milestone contract, and the risk-tier sign-offs in `AGENTS.md`.
- Promoting any future capability to a separate process requires passing the §2 service-split test and
  a High-risk sign-off.

---

## Explicitly not decided / not authorised here

- No new service, database, message bus, or queue beyond the planned Redis.
- No LLM integration is approved; the first LLM integration is itself a gated decision.
- No new schema, migration, state, event type, or contract change.
- No YouTrack ticket is opened by this ADR.

---

## Supersedes

None.

## Superseded by

None.
