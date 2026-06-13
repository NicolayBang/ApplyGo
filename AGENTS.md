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

## Architecture Governance

- Architecture diagrams must reflect implemented behavior.
- Documentation must not describe functionality that does not exist.
- When implementation and documentation disagree, investigate and reconcile before merge.
- Future-state architecture is allowed but must be clearly labeled:
  - Future Architecture
  - Planned
  - Not Implemented
- Source-of-truth hierarchy for implemented behavior:
  1. Implemented code
  2. Architecture decision records and architecture documentation
  3. Diagrams
- Diagrams are explanatory artifacts, not authoritative specifications.
- Pull requests that modify architecture-related code should review associated diagrams for drift.

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

## AI Roles

### Archi — Architecture Lead

Owns:

- Architecture decisions
- ADRs
- Tradeoff analysis
- Long-term system design
- Architecture consistency

Does not implement code.

### Dick — DevOps / Governance Reviewer

Owns:

- Architecture enforcement
- PR review guidance
- Risk assessment
- Process discipline
- Drift detection

Does not approve merges automatically.

### Copilot / Codex

Owns:

- Scoped ticket implementation
- Code changes
- Test updates
- Documentation updates

Must not invent architecture.

Must follow approved architecture and contracts.

---

## Virtual Team Routing

Virtual personas advise only.

Humans own final decisions.

Use `docs/team/dick.md` for DevOps, repo workflow, PR process, environments, CI/CD, governance, and architecture drift.

Use `docs/team/architect.md` for system architecture, domain modeling, state machines, event flows, data model alignment, architecture drift, and technical tradeoff review.

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

## Repository Naming Convention

Use this convention for new work only. Do not rename existing branches, commits, or PRs.

### Tickets

Format:

`M<milestone>-APP-###`

Example:

`M1-APP-002` - Add Cloud Development Environment

Tickets are for planning and traceability.

### Branches

Format:

`feature/M<milestone>-<short-description>`
`docs/M<milestone>-<short-description>`
`fix/M<milestone>-<short-description>`

Examples:

`feature/M1-codespaces-support`
`feature/M1-state-machine-foundation`
`docs/M1-virtual-team-personas`

Branches should be readable at a glance and show the roadmap milestone.

### Commits

Use Conventional Commits.

Examples:

`feat(devops): add codespaces support`
`docs: add virtual team persona routing`
`fix(db): correct migration ordering`

Commits describe the actual change.

### Transition Rule

Existing APP-001 and APP-002 branch names remain unchanged.
Apply this convention only to future work.

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

---

## PR and Merge Process

Default rule:

- Do not push directly to main.
- Use a branch + PR for all changes that affect repository history.

Exceptions:

- Direct main progression is allowed only when explicitly approved by humans.

Governance-only changes:

- Still use a PR when possible, even if low risk.
- If GitHub cannot open a PR because there is no head/base diff, do not create fake changes just to force a PR.
- Treat the work as closed with push evidence and human signoff.

Dick / DevOps persona should enforce this process and flag uncertainty before merge.

---

## Dev Environment

- Local Docker and GitHub Codespaces are both supported.
- `docker-compose.yml` is the shared source of truth.
- No machine-specific setup should be required.
- Environment changes must be documented.

---

## Repository Naming Convention

Rules:

- Do not rename existing branches or commits.
- Existing APP-001 and APP-002 history remains unchanged.
- Apply the new convention only to future work.

Ticket names use milestone + ticket ID:

`M1-APP-002 - Add Cloud Development Environment`

Branch names use milestone + short description:

- `feature/M1-codespaces-support`
- `feature/M1-policy-engine`
- `docs/M1-devops-guide`
- `fix/M1-migration-ordering`

Commits use Conventional Commits:

- `feat(devops): add codespaces support`
- `docs: define repository naming conventions`
- `fix(db): correct migration ordering`

Purpose:

- Tickets are for planning and traceability.
- Branches are for readable development workflow.
- Commits describe the actual change.

---

## Dick Persona Testing Guidance

Dick may act as architecture advisor and implementation support.

For architecture-critical work, create runnable test classes during implementation.
Tests must be executable by the project test runner, not just pseudocode.
Prefer pytest-based test files under the existing backend test structure.

Include clear test cases for:

- Valid state transitions.
- Invalid transition rejection.
- Event logging.
- FK/database constraints.
- Audit logs not cascade-deleting.
- Executor idempotency.
- Policy decision before execution.

Any PR touching state machine, DB schema, event log, policy, executor, or contracts should include runnable tests or explain why tests are deferred.

### Copilot Validation Delegation

When required validation depends on GitHub-hosted services, Codespaces, CI, PostgreSQL, Redis, or another environment not running locally, Dick should default to requesting Copilot agent validation in the pull request.

The request should be posted as a PR comment and include:

- The exact commands to run.
- The expected environment, such as Codespaces or GitHub Actions.
- The specific migration, test suite, or quality gate being validated.
- The confirmation expected from Copilot before merge.

Do not rerun redundant local checks after GitHub CI or Copilot has already validated the same commands, unless the PR changed again, CI failed, or a human explicitly asks for local verification.

For docs-only PRs, do not run backend tests unless the documentation change modifies executable examples, test policy, architecture-critical contracts, or migration instructions.
