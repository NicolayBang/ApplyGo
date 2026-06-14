# Frontend Design Handoff

**Status:** Sketching guidance only  
**Audience:** frontend design reviewers, Codex/Copilot agents, Vanessa persona  
**Scope:** M1 dashboard visual/layout exploration before implementation

This note captures guardrails for frontend design exploration. It is not an implementation request
and does not authorize changing product scope, backend behavior, workflow logic, or architecture.

## Design Goal

Improve reviewer clarity and visual polish for the existing M1 dashboard while preserving the
governed automation story:

```text
Sample job -> Create -> Score -> state progression -> Policy -> Dry-run -> audit timeline
```

The UI should feel like a clean, modern SaaS workflow tool, not a marketing page or mass-apply bot.

## Preferred Direction

The strongest MVP direction is a hybrid of:

- a guided flow/progress rail that makes the state machine visible;
- a focused review workspace that keeps one application, next action, policy, dry-run, and audit
  evidence easy to inspect.

A pipeline/board view may be useful later, but it should not replace the one-application governed
demo flow before M1 is complete.

## Must Preserve

- Existing backend API contracts.
- Existing dashboard route behavior.
- Existing state names and transition constraints.
- Policy-before-executor ordering.
- Dry-run-only external action behavior.
- Audit timeline visibility.
- Review readiness visibility.
- The Sample job happy path.
- Disabled dry-run behavior when policy returns `review` or `deny`.

## Do Not Add During Sketching

- New backend endpoints.
- New state machine behavior.
- Real submission, Gmail, browser, or LLM automation.
- New frontend framework or build system.
- New architecture scope.
- Product promises beyond the implemented M1 workflow.

## Implementation Readiness Checklist

Before turning sketches into code, confirm:

- the selected layout still supports the complete M1 demo path;
- all key evidence remains visible without hunting through hidden tabs;
- mobile/narrow viewport behavior is considered;
- button labels and badges fit their containers;
- visual changes can be implemented as a small PR with focused validation;
- screenshots or manual notes are attached to the PR for reviewer confidence.
