# ApplyGo Brand Transition

**Status:** Draft brand direction  
**Audience:** Nicolay, Francis, Vanessa persona, frontend design reviewers  
**Scope:** naming guidance only; no implementation rename is authorized by this document

The intended product brand direction is **ApplyGo**.

The repository, backend package names, existing docs, dashboard labels, API names, database names,
and migration history remain **ApplyPilot** until the team opens and approves a separate rename PR.

## Current Naming Rule

- Use **ApplyGo** in visual sketches, logo exploration, brand concepts, and presentation mockups.
- Keep **ApplyPilot** in implemented code, committed UI text, architecture docs, contracts, package
  names, database objects, CI, and repository workflow.
- Do not mix names inside implemented product screens unless a dedicated rename PR is in scope.
- Do not rename the GitHub repository, Python package, database names, migrations, or historic
  branches as part of MVP dashboard polish.

## Why The Rename Is Deferred

Renaming the implemented product touches many surfaces:

- dashboard title and visible UI labels;
- README and capstone documentation;
- architecture and contract references;
- screenshots and validation notes;
- backend configuration;
- package names and import paths if the technical rename ever expands that far;
- CI and deployment documentation.

A clean transition should happen intentionally, with review, instead of being bundled into unrelated
frontend polish.

## Future Rename PR Shape

A future rename PR can decide how far the transition goes:

- brand-only visible UI change;
- documentation wording change;
- repository display name change;
- package/runtime rename;
- database/config rename.

For MVP, prefer a brand-only or documentation-only step before any package, database, or migration
rename.

## Guardrail

ApplyGo should strengthen the product story: guided, controlled, transparent job application
workflow. It should not push the product toward mass-apply or uncontrolled automation messaging.
