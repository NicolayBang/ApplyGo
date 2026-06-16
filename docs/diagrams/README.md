# Diagram Index

This folder contains explanatory diagrams for ApplyGo. Diagrams help reviewers understand the
system, but they are not the source of truth for implemented behavior.

Authority remains:

1. implemented code and migrations
2. approved ADRs and architecture documentation
3. contracts
4. diagrams

## Current Diagrams

- `component-diagram.md` - high-level component relationships.
- `database-schema.md` - implemented schema through packet review persistence and company identity plus planned future ER view.
- `state-machine.md` - implemented M1 application workflow states.
- `execution-sequence.md` - transition validation, packet review persistence, and guarded submission ordering.
- `backend-class-diagram.md` - backend class and module reference including company identity and packet review persistence.

## Maintenance Rule

When behavior changes, update the authoritative code/docs first, then update diagrams so they remain
useful explanatory artifacts.
