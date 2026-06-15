# Capstone Presentation Backlog

**Status:** Optional polish backlog  
**Scope:** Recruiter/instructor presentation quality, not new product scope

This list captures small improvements that would make ApplyPilot easier to review and more polished
as a portfolio/capstone project. These items do not change M1 architecture or authorize new
automation behavior.

## Highest Impact Before Sharing Widely

- [ ] Merge the M1 dashboard workflow validation PR after manual validation is accepted.
- [ ] Run one final manual demo on current `main`.
- [x] Record a dated M1 validation note after the first live manual demo pass.
- [ ] Add one dashboard screenshot or short GIF to the README.
- [x] Add a GitHub Actions CI badge to the README.

## Reviewer Experience Improvements

- [x] Add a compact architecture diagram to the README:
  `Dashboard -> FastAPI -> Tracker -> PostgreSQL -> Event Log / Policy / Executor`.
- [x] Add a short "Key tradeoffs" section to `docs/capstone/reviewer-brief.md`:
  dry-run first, policy before executor, explicit non-goals, and why real automation is deferred.
- [x] Make the Codespaces demo path more one-click friendly if the repo is shared with reviewers.
- [ ] Keep final validation notes and any selected screenshots close to the top-level reviewer path.

## Product Polish Candidates

- [ ] Add an audit report export/download option for the current application.
- [ ] Improve dashboard mobile spacing and dense helper text.
- [ ] Improve empty states and reviewer-facing labels without changing backend behavior.
- [ ] Add a small roadmap/issues section linking future milestones to planned GitHub issues.

## Later Portfolio Upgrades

- [ ] Host a safe demo environment after M1 is stable.
- [ ] Add a short demo video once the UI is final enough.
- [ ] Implement one real external integration only in a governed dry-run mode first, such as a
  Gmail draft preview or document packet generator.

## Guardrails

- Do not add real Gmail, browser, or submission side effects as presentation polish.
- Do not blur implemented M1 behavior with planned M2/M3 work.
- Do not expand MVP scope without an explicit human decision.
- Keep AI-assisted development disclosure professional and brief.
