# M2 Packet Preview Validation

Status: Draft validation checklist
Milestone: M2 application packet preparation and review

Use this checklist after the M1 dashboard path is running. It validates the implemented M2 packet
preview behavior without approving persistence, migrations, external automation, or LLM-dependent
drafting.

## Preconditions

- Backend is running at `http://localhost:8000`.
- Dashboard is open at `http://localhost:8000/ui/`.
- A sample or real application has been created or loaded.
- The M1 score, policy, and dry-run path has been exercised when validating full packet evidence.

## Checklist

| # | Check | Expected result |
|---|-------|-----------------|
| 1 | Open or load an application in the dashboard. | Application summary, review readiness, and audit timeline render. |
| 2 | Inspect the Application packet panel. | The panel shows generated packet text from current review evidence. |
| 3 | Score the application. | Packet text updates with fit score, confidence, recommendation, reasons, risks, missing data, and red flags. |
| 4 | Evaluate policy. | Packet text includes the latest policy decision and required review details when present. |
| 5 | Run Preview action when policy allows it. | Packet text includes executor status, safeguards, planned steps, and no-side-effect evidence. |
| 6 | Inspect the Deterministic Cover Note Draft section. | Draft references the role, company, recommendation, score when present, one reason, and one risk or blocker. |
| 7 | Click Copy cover note. | Status reports that the deterministic cover-note draft was copied, unless browser clipboard permission blocks it. |
| 8 | Click Copy packet. | Status reports that the full packet preview was copied, unless browser clipboard permission blocks it. |
| 9 | Refresh or reload the application. | Packet content regenerates from audit data; no new packet rows or external side effects are created. |

## Pass Criteria

- The packet preview stays deterministic for the same loaded evidence.
- The cover-note draft is clearly review-only.
- Copy actions do not call backend write routes.
- No email, browser automation, external submission, packet persistence, or LLM call occurs.
- Existing M1 dashboard workflow behavior remains intact.

## Notes

This checklist covers the current read-only packet slice only. Persisted packet review decisions
will need separate backend tests, audit-event tests, and human review before implementation.
