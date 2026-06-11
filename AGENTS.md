# AGENTS.md — ApplyPilot

## Project Identity

ApplyPilot is a governed job application automation platform.

It is not a loose autonomous AI bot.

The system is built around workflow control, policy enforcement, auditability, dry-run execution, and human review.

---

## Architecture Authority

Source of truth priority:

1. `docs/architecture/OpenClaw_Final_Agreed_Architecture.pdf`
2. Approved ADRs
3. `docs/architecture/`
4. `docs/contracts/`
5. `AGENTS.md`
6. Chat discussions

If implementation, documentation, or agent output conflicts with the architecture PDF, treat it as architecture drift unless explicitly superseded by an approved ADR.

---

## Core Architecture Rules

- Workflow owns state.
- Database owns truth.
- Policy engine owns permission.
- LLMs assist only with extraction, classification, scoring support, and drafting.
- Workers execute approved actions only through a shared executor contract.
- Dry-run is a first-class capability.
- Semi-auto and full-auto are policy modes on the same workflow.
- All important decisions and executions must be auditable.

---

## Required Execution Flow

Policy Check  
→ Log Policy Decision  
→ Executor Dry Run or Execute  
→ Log Execution Result  
→ Update Workflow State  

Never bypass policy.

Never execute before recording a policy decision.

Never update workflow state without recording execution results.

---

## Virtual Team Routing

Virtual personas advise only.

Humans own final decisions.

Use `docs/team/dick.md` for DevOps, repo workflow, PR process, environments, CI/CD, governance, and architecture drift.

Use `docs/team/vanessa-brand-designer.md` for logo, branding, color, typography, visual identity, and marketing visuals.

Copilot / Codex may implement scoped code, test, and documentation changes only when asked. It must not invent architecture and must follow approved architecture and contracts.

---

## Human Authority

Nicolay and Francis are the final authority.

AI may suggest, review, challenge, draft, and implement.

Humans decide, approve, merge, and own the design.

---

## MVP Scope

Minimum demo:

Manual Job Input  
→ Parse / Classify  
→ Score  
→ Policy Check  
→ Dry-Run Execution Plan  
→ Event Log  
→ Dashboard / Tracker View  

Out of scope:

- Gmail automation
- Browser automation
- Full-auto submissions
- Kubernetes
- Microservices
- Complex agent orchestration
- Production deployment automation

---

## Backend Priorities

Implement in this order:

1. Canonical data model
2. State machine
3. Event log
4. Policy engine
5. Executor contract
6. Dry-run executor
7. Basic API endpoints
8. Dashboard integration

---

## Repository Structure

ApplyPilot/
├── AGENTS.md
├── README.md
├── .env.example
├── docker-compose.yml
├── backend/
├── frontend/
└── docs/
	├── architecture/
	├── contracts/
	├── decisions/
	├── diagrams/
	└── team/

---

## Naming Conventions

### Python

- files: `snake_case.py`
- functions: `snake_case`
- variables: `snake_case`
- classes: `PascalCase`
- constants: `UPPER_SNAKE_CASE`

### Documentation

- markdown: `kebab-case.md`
- ADRs: `ADR-0001-short-title.md`
- contracts: `domain-contract.md`

### Branches

- `feature/APP-001-short-description`
- `docs/APP-001-short-description`
- `fix/APP-001-short-description`

### Commits

- `feat: add state machine foundation`
- `fix: correct policy evaluation bug`
- `docs: add architecture documentation`
- `test: add executor contract tests`

---

## Engineering Rules

- Prefer simplicity over cleverness.
- Prefer explicit contracts over hidden behavior.
- Prefer small PRs.
- Keep worker boundaries clear.
- Add tests for workflow-critical logic.
- Avoid premature abstraction.
- Avoid premature scaling.
- Preserve auditability.
- Preserve deterministic behavior.
- Preserve dry-run support.

---

## Branch, Commit, Migration, and Merge Discipline

- Do not mix governance/docs commits with backend implementation commits.
- Use scoped branches such as `feature/APP-001-backend-spine`.
- Group commits by concern: models, migrations, service wiring, tests, docs.
- Keep Alembic migrations in dedicated commits.
- Before committing migrations, verify they are deterministic and aligned with the canonical data model.
- Run gates before merge: ruff, pytest, alembic upgrade head, backend starts, /health works.
- If code, models, states, or workflow behavior conflict with the locked architecture PDF, stop and flag architecture drift.
- Do not resolve architecture drift silently.
- Resolve drift only by aligning code to the PDF or creating an approved ADR.
