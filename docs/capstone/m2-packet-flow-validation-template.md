# M2 Packet Flow Validation Template

**Status:** Reusable manual validation template  
**Milestone:** M2 application packet preparation and review  
**Use when:** validating the current packet preview and persisted human packet review flow

This template is meant to be reused for PR signoff, capstone review sessions, and live walkthroughs.
It keeps the packet preview path and packet review persistence path in one place so the reviewer can
record what was tested, what passed, and what remains intentionally out of scope.

## Session Header

Copy this section into the validation note for the current session.

```md
# M2 Packet Flow Manual Validation

- Date:
- Reviewer:
- Branch / PR:
- Environment:
- Backend URL:
- Dashboard URL:
- Database:
- Seeded sample used:
- Result: Pass / Pass with notes / Blocked
```

## Preconditions

Mark each line before running the detailed checks.

- [ ] Backend is running at `http://localhost:8000`.
- [ ] Dashboard is open at `http://localhost:8000/ui/`.
- [ ] PostgreSQL migrations are applied through the current packet-review migration.
- [ ] A sample or real application has been created or loaded.
- [ ] Score, policy, and preview evidence can be exercised on the selected application.
- [ ] The Application packet panel is visible.

## Validation Table

Use `Pass`, `Fail`, `Blocked`, or `N/A` in the `Result` column.

| # | Area | Check | Expected result | Result | Notes / evidence |
|---|------|-------|-----------------|--------|------------------|
| 1 | Load | Open or load an application in the dashboard. | Application summary, review readiness, packet panel, and audit timeline render. |  |  |
| 2 | Packet preview | Inspect the Application packet panel. | Packet text is generated from current job, score, policy, executor, and audit evidence. |  |  |
| 3 | Score evidence | Score the application. | Packet text updates with fit score, confidence, recommendation, reasons, risks, missing data, and red flags. |  |  |
| 4 | Policy evidence | Evaluate policy. | Packet text includes the latest policy decision and any required human review details. |  |  |
| 5 | Preview evidence | Run Preview action when policy allows it. | Packet text includes executor status, safeguards, planned steps, and no-side-effect evidence. |  |  |
| 6 | Cover note | Inspect the deterministic cover-note draft. | Draft references role, company, recommendation, score when present, and at least one reason or blocker. |  |  |
| 7 | Copy controls | Click Copy cover note and Copy packet. | Status reports success unless browser clipboard permission blocks it. |  |  |
| 8 | Download control | Click Download packet. | A text file is downloaded with the generated packet preview. |  |  |
| 9 | Review form | Enter optional reviewer notes before submission. | Notes stay local until a packet review decision is submitted. |  |  |
| 10 | Review decision | Click Approve packet, Request changes, or Reject packet. | Status reports that packet review was recorded without external side effects. |  |  |
| 11 | Readiness summary | Inspect Review readiness after recording the packet review. | The Packet review card shows the latest recorded decision. |  |  |
| 12 | Packet status | Inspect the packet panel status after recording the decision. | The panel shows the latest packet review decision, reviewer, and source. |  |  |
| 13 | Audit timeline | Inspect Audit timeline. | `application_packet.reviewed` appears after a recorded packet review. |  |  |
| 14 | Audit payload | Inspect the review event payload if needed. | Payload includes review id, decision, reviewer, source, and flags; it does not include full packet text. |  |  |
| 15 | Refresh | Refresh or reload the same application. | Packet preview regenerates from evidence and latest packet review remains visible from persisted backend data. |  |  |

## Pass Criteria

- Packet preview remains deterministic for the same loaded evidence.
- Human packet review persists and is visible in the current dashboard read model.
- `application_packet.reviewed` is appended when a review is recorded.
- Review controls make clear that no email, browser automation, or submission occurred.
- Full packet text is not written into the audit event payload.
- Existing score, policy, preview, and audit behavior remains intact.

## Out of Scope

This template does not approve:

- Gmail sending
- browser automation
- real application submission
- executor or policy side effects
- OpenClaw integration
- required LLM generation
- long-term packet archival beyond the implemented review evidence boundary

## Suggested Evidence to Attach

- screenshot of the Application packet panel after score/policy/preview
- screenshot of recorded packet review status/history
- screenshot of the audit timeline showing `application_packet.reviewed`
- brief note if clipboard or download behavior was blocked by browser permissions

## Related Docs

- `m2-packet-preview-validation.md` for the narrower preview-only checklist
- `m2-packet-review-validation.md` for the narrower review-persistence checklist
- `dashboard-demo-flow.md` for the broader implemented workflow walkthrough
