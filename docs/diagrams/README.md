# Diagram Index

This folder contains explanatory diagrams for ApplyPilot. Diagrams help reviewers understand the
system, but they are not the source of truth for implemented behavior.

Authority remains:

1. implemented code and migrations
2. approved ADRs and architecture documentation
3. contracts
4. diagrams

## Current Diagrams

- `component-diagram.md` - separate implemented M1 and planned future component relationships.
- `database-schema.md` - implemented M1 database view plus planned future ER view.
- `state-machine.md` - implemented M1 states plus a clearly labeled proposed future projection.
- `execution-sequence.md` - policy, executor, and audit ordering.
- `backend-class-diagram.md` - backend class and module reference.

## Maintenance Rule

When behavior changes, update the authoritative code/docs first, then update diagrams so they remain
useful explanatory artifacts.
