# ApplyGo Brand Transition

**Status:** Approved Phase 1 public brand direction  
**Audience:** Nicolay, Francis, Vanessa persona, frontend design reviewers  
**Scope:** public naming guidance and visible brand transition only; runtime rename is not authorized by this document

The product brand is now **ApplyGo** for public-facing materials and visible UI.

The backend package names, API service name, database names, migration history, and internal runtime
identifiers remain **ApplyPilot** / `applypilot` until the team opens and approves a separate
technical rename PR.

## Current Naming Rule

- Use **ApplyGo** in public-facing docs, recruiter/reviewer materials, visible dashboard branding,
  presentation mockups, and logo exploration.
- Keep **ApplyPilot** / `applypilot` in package names, import paths, health payloads, database
  objects, migrations, CI wiring, and technical architecture references unless a dedicated technical
  rename PR is in scope.
- It is acceptable during Phase 1 for public docs and UI to say ApplyGo while runtime commands and
  service identifiers still say `applypilot`.
- Do not rename the Python package, database names, migrations, or historic branches as part of
  this public branding pass.

## Why The Technical Rename Is Deferred

Renaming the technical implementation touches many surfaces:

- backend configuration;
- package names and import paths if the technical rename ever expands that far;
- CI and deployment documentation.

The public-facing rename is safe to do first. The deeper technical rename should happen
intentionally, with review, instead of being bundled into unrelated frontend or milestone work.

## Phase Plan

### Phase 1: public brand pass

- README and reviewer-facing docs say **ApplyGo**;
- visible dashboard branding says **ApplyGo**;
- demo language uses the ApplyGo product name;
- repo readers are told that internal runtime identifiers still say `applypilot`.

### Phase 2: technical rename pass

A later technical rename PR can decide how far the transition goes:

- repository display name change;
- repository slug change;
- package/runtime rename;
- database/config rename.

For this milestone, prefer the Phase 1 public brand pass before any package, database, or migration
rename.

## Guardrail

ApplyGo should strengthen the product story: guided, controlled, transparent job application
workflow. It should not push the product toward mass-apply or uncontrolled automation messaging.
