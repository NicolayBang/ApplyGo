# Locked Plan

This repository follows the uploaded final architecture document as the implementation baseline.

Implementation must not deviate from these core decisions without explicit review:

- canonical data model as source of truth
- explicit application state machine
- append-only event log
- policy engine with manual, semi-auto, full-auto, and dry-run
- executor contract with `execute` and `dry_run`
- worker boundaries for Gmail, documents, and browser actions
- dry-run support from day one
- idempotency keys on executor actions
- confidence and explanation schema
- deterministic error taxonomy and fallback behavior
- worker-specific secret boundaries
- v1 non-goals enforced

The first milestone is the platform spine only. Feature workers remain placeholders until the control plane is proven.
