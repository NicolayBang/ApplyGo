# M2 Packet Review Validation

Status: Draft validation checklist
Milestone: M2 application packet preparation and review

Use this checklist after the packet preview and packet review persistence path are running. It
validates that a human can record a packet decision without creating external side effects.

## Preconditions

- Backend is running at `http://localhost:8000`.
- Dashboard is open at `http://localhost:8000/ui/`.
- PostgreSQL migrations are applied through `0008`.
- A sample or real application has been created or loaded.
- The packet panel is visible and the Application ID field contains a valid application UUID.

## Checklist

| # | Check | Expected result |
|---|-------|-----------------|
| 1 | Load an application in the dashboard. | Application summary, review readiness, packet panel, and audit timeline render. |
| 2 | Inspect the Application packet panel. | Packet text is generated from current job, score, policy, executor, and audit evidence. |
| 3 | Enter optional reviewer notes. | Notes stay local until a packet review decision is submitted. |
| 4 | Click Approve packet, Request changes, or Reject packet. | Status reports that packet review was recorded. |
| 5 | Inspect Review readiness. | The Packet review card shows the latest recorded decision. |
| 6 | Inspect the packet panel status. | The panel shows the latest packet review decision, reviewer, and source. |
| 7 | Inspect Audit timeline. | `application_packet.reviewed` appears as the latest event. |
| 8 | Inspect the event payload if needed. | Payload includes review id, decision, reviewer, source, and flags; it does not include full packet text. |
| 9 | Refresh or reload the same application. | Latest packet review remains visible from persisted backend evidence. |

## Pass Criteria

- Packet review decisions persist in `application_packet_reviews`.
- `application_packet.reviewed` is appended when a review is recorded.
- Review summary returns `latest_packet_review`.
- Dashboard review controls make clear that no external action occurred.
- Full packet text is not sent by the dashboard review action.
- No email, browser automation, application submission, OpenClaw action, or LLM call occurs.
- Existing M1 score, policy, dry-run, and audit behavior remains intact.

## Automated Coverage

Current automated checks include:

- ORM/schema tests for packet review constraints and retention behavior.
- PostgreSQL-backed tests for valid nullable packet text and invalid value rejection.
- Tracker tests for packet review persistence and audit event payload shape.
- API tests for packet review creation, invalid decisions, missing applications, and review summary visibility.
- Dashboard asset contract tests for packet review controls and API route wiring.

## Boundaries

This checklist validates human packet review evidence only. It does not approve:

- Gmail sending;
- browser automation;
- real application submission;
- policy or executor side effects;
- OpenClaw integration;
- required LLM generation;
- storing full packet text from the dashboard review action.
