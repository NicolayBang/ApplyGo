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

### Derek — DevOps / Governance Reviewer

Owns:

- Architecture enforcement
- PR review guidance
- Risk assessment
- Process discipline
- Drift detection

Does not approve or perform merges unless explicitly instructed by a human.

### Claude Code / Copilot / Codex

Owns:

- Scoped ticket implementation
- Code changes
- Test updates
- Documentation updates

Must not invent architecture.

Must follow approved architecture and contracts.

---

## AI Instruction Files

- `AGENTS.md` is the canonical repository-wide instruction file.
- `CLAUDE.md` is a committed Claude Code adapter that imports `AGENTS.md`.
- Do not duplicate repository rules in `CLAUDE.md`; update `AGENTS.md` instead.
- `CLAUDE.local.md` is reserved for machine- or user-specific Claude Code preferences and is ignored by Git.

---

## Agent Change Visibility

Agents must make repository state and change scope explicit while they work.

Before any material action, including branch changes, file edits, commits, pushes, pull requests,
migrations, or destructive commands, the agent must state:

- the current branch or explicitly state that the action is read-only
- the branch that will be modified
- the files, systems, or behavior expected to change
- what will remain intact and outside the task scope
- whether the action is proposed, in progress, completed, or blocked

When the working branch changes, the agent must announce the change before running the command and
confirm the resulting branch afterward. Work from another branch or pull request must not be
described as modified when it is only being inspected or used as context.

Before editing files, the agent must identify the exact intended edit scope. After editing, the
agent must report the actual changed files and call out any difference from the stated scope.

Before committing or pushing, the agent must summarize what is staged and explicitly confirm that
unrelated files, branches, commits, and open pull requests remain intact. Final responses must state
the branch modified, commit or PR status when applicable, validation performed, and untouched scope.

Agents must distinguish observed state from intended or proposed state. Do not describe a proposed
change as implemented, a running check as passed, or an unmerged branch as part of `main`.

ALL CAPS may be used sparingly to draw attention to sensitive operations such as destructive
commands, direct changes to `main`, migration execution, secret handling, force pushes, branch
replacement, or scope changes. Routine progress should use normal capitalization so sensitive
warnings remain visually meaningful.

If the agent cannot determine the active branch, change scope, or preservation boundary, it must
stop and verify before modifying the repository.

---

## Remote Validation Assist

Remote Validation Assist replaces the temporary five-PR Experiment Mode trial. Use it selectively
when remote validation adds real confidence, not as a default ceremony for every PR.

Codex owns the main implementation thread, architecture interpretation, final integration, and final
recommendation. Copilot or another GitHub agent may be asked to provide bounded support only when the
task benefits from a remote environment or independent check.

Use Remote Validation Assist when:

- PostgreSQL is required and is not running locally.
- A migration, database retention rule, policy contract, executor contract, or deployment setup needs
  Codespaces or CI validation.
- GitHub CI fails and remote logs or reruns are needed.
- Browser, Codespaces, or GitHub-hosted behavior cannot be fully checked locally.
- A narrow missing-test or stale-reference check can be delegated without architecture judgment.

Do not use Remote Validation Assist when:

- The PR is docs-only and `git diff --check` plus scoped review are sufficient.
- Local tests fully cover the change.
- The task requires architecture decisions, product direction, secrets, broad refactors, or migration
  design.
- Prompting and reviewing another agent would cost more time than doing the check directly.

Delegated tasks must name the exact branch or PR, files or behavior in scope, commands or checks to
run, expected result, and what must not be changed. Delegated tasks must be small enough to review
quickly and must not authorize the other agent to merge pull requests unless a human explicitly
allows it.

Results from delegated agents are advisory until reviewed and reconciled by Codex or a human.

PR descriptions should record remote validation only when it is used. Timing notes are optional and
should be used for unusual blockers, new workflow experiments, or when a human explicitly asks for
speed tracking.

Remote Validation Assist does not override architecture authority, human final decision-making, PR
discipline, testing requirements, security boundaries, or merge rules.

---

## Virtual Team Routing

Virtual personas advise only.

Humans own final decisions.

Use `docs/team/derek.md` for DevOps, repo workflow, PR process, environments, CI/CD, governance, and architecture drift.

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
├── CLAUDE.md
├── README.md
├── .env.example
├── docker-compose.yml
├── backend/
├── frontend/
└── docs/
	├── architecture/
	├── contracts/
	├── codebase/
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

Derek / DevOps persona should enforce this process and flag uncertainty before merge.

Low-risk documentation auto-merge exception:

- Derek may mark ready and merge a docs-only pull request without additional human instruction when all of the following are true:
  - the PR changes only low-risk documentation files such as `README.md`, `docs/**/*.md`, or other non-authoritative Markdown reference pages;
  - the PR does not modify application code, tests, migrations, contracts, architecture authority, `AGENTS.md`, `CLAUDE.md`, CI/workflow files, security-sensitive files, or executable examples;
  - GitHub CI has completed successfully;
  - the PR is mergeable, up to date enough for GitHub to merge, and has no unresolved review feedback or requested changes;
  - the PR body or comments explain why tests were not required, when applicable.
- If any criterion is unclear, Derek must stop and ask for human instruction before merging.
- For all non-low-risk PRs, Derek cannot merge pull requests unless a human explicitly instructs him to merge that PR.

### Auto-Merge Mode

Auto-Merge Mode is an explicit, temporary operating mode. It is inactive by default and starts only
when a human says to enable Auto-Merge Mode.

Default activation:

- maximum window: 3 PRs;
- scope: next logical ApplyPilot work;
- allowed risk level: low-to-medium only;
- Copilot or remote-agent review: required when useful for validation, CI/environment checks, or
  governance/architecture consistency;
- merge permission: Codex may merge after CI passes, required validation is complete, requested
  Copilot/remote review has been reconciled, and Codex is comfortable with the diff;
- stop condition: after 3 successful merges, return to normal human-confirmed merge behavior.

Humans may override any default activation detail. Explicit human overrides win unless they conflict
with repository safety rules, human authority, security boundaries, or the hard exclusions below.
If an override is unclear or unsafe, Derek/Codex must ask before merging anything.

Auto-Merge Mode may merge a PR only when all of the following are true:

- the PR is inside the human-approved scope and remaining merge window;
- the changed files match the approved risk level;
- GitHub CI has completed successfully on the current head commit;
- the PR is mergeable and has no unresolved review feedback, requested changes, or conflicts;
- local validation appropriate to the change has passed, or remote validation has been requested and
  reviewed when local validation is not enough;
- Copilot or another remote agent has provided the requested review/validation when the activation
  requires it;
- the PR body or comments record what was validated and why any tests were not required;
- Codex has reviewed any remote-agent changes before merging.

Auto-Merge Mode must not merge a PR without fresh human instruction when the PR touches:

- application code;
- tests;
- Alembic migrations or database schema behavior;
- contracts that authorize implementation;
- architecture authority or approved ADRs;
- `AGENTS.md` or `CLAUDE.md`;
- CI/workflow files;
- security-sensitive files;
- secrets, credentials, or deployment permissions.

Copilot review prompts in Auto-Merge Mode must be narrow and auditable. They must name the exact PR,
files or behavior in scope, expected validation, reference documents, and what Copilot must not
change. Copilot results are advisory until Codex reviews them.

When the Auto-Merge Mode stop condition is reached, Derek/Codex must stop auto-merging, clean up any
finished branches when safe, report the merged PRs and any issues encountered, and return to normal
human-confirmed merge behavior.

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

## Derek Persona Testing Guidance

Derek may act as architecture advisor and implementation support.

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

When required validation depends on GitHub-hosted services, Codespaces, CI, PostgreSQL, Redis, or another environment not running locally, Derek should default to requesting Copilot agent validation in the pull request.

The request should be posted as a PR comment and include:

- The exact commands to run.
- The expected environment, such as Codespaces or GitHub Actions.
- The specific migration, test suite, or quality gate being validated.
- The confirmation expected from Copilot before merge.

Do not rerun redundant local checks after GitHub CI or Copilot has already validated the same commands, unless the PR changed again, CI failed, or a human explicitly asks for local verification.

For docs-only PRs, do not run backend tests unless the documentation change modifies executable examples, test policy, architecture-critical contracts, or migration instructions.
