# MVP Status

**Status:** Milestone 1 platform spine implemented

**Audience:** reviewers, instructors, recruiters, and contributors

**Last updated:** 2026-06-14

ApplyPilot is currently a governed job application automation platform spine, not a finished job
application product. The implemented system proves the core workflow, persistence, policy, dry-run,
and audit model needed before adding external automation.

## Implemented

- Manual job intake through the dashboard.
- Deterministic job metadata classification for M1 demo fields.
- Durable PostgreSQL persistence for jobs, applications, policy decisions, executor actions, and
  audit events.
- Application state machine with guarded transitions.
- Event log for application creation, state changes, scoring, policy decisions, and executor
  activity.
- Policy engine with manual, semi-auto, full-auto, and dry-run mode handling.
- Stub executor that produces side-effect-free dry-run plans.
- Dashboard view for tracker state, scoring, policy, executor records, and audit timeline.
- Docker Compose PostgreSQL/Redis services, one-shot migration runner, and optional demo seed
  validation.
- CI gates for backend quality, migrations, tests, and frontend syntax.

## Demo Path

The current reviewer demo is:

```text
manual intake -> parse/classify -> state progression -> scoring -> policy check -> dry-run executor -> audit timeline
```

Use `docs/capstone/dashboard-demo-flow.md` for the step-by-step runbook.

## Not Implemented Yet

- Real external application submission.
- Gmail automation.
- Browser automation.
- LLM extraction or drafting.
- Multi-user authentication.
- Production deployment.
- Normalized company/contact/document/thread future tables.

## Next Product Direction

The next architecture-safe direction is to keep implementation contract-first:

- approve or reject the proposed M3 company identity and migration contracts;
- only then add the `companies` schema, ORM/API compatibility, migration, and PostgreSQL-backed
  tests;
- keep external side effects behind policy checks, dry-run behavior, and human oversight.

## Reviewer Signal

This repository currently demonstrates:

- architecture-first development;
- database-backed workflow design;
- migration discipline;
- CI and Compose-based validation;
- auditability and policy enforcement;
- careful separation between implemented behavior and planned future capabilities.
