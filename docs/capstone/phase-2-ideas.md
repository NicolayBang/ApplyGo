# Phase 2 Ideas - Parking Lot

> **Status:** Not committed scope. This is a capture list so we don't forget to discuss + prioritize after MVP ships.
> **Ground rules still apply:** workflow owns state, DB owns truth, policy owns permission, everything stays auditable through the event log. Nothing here should bypass the state machine, the policy engine, or the executor contract.

---

## 1. Application status listeners

_From the thread: tracker listeners that check the status of submitted applications, post-MVP._

- Background workers that periodically check the status of applications already submitted.
- Drive transitions like `APPLIED -> CONFIRMED -> INTERVIEW / REJECTED` instead of leaving the tracker stale after submit.
- Candidate signals: recruiter emails (ties directly into M7 email classification), ATS confirmation emails, ATS status pages.
- Listeners **propose** transitions - they do not mutate state directly. State still changes only through the state machine.
- Every status check + resulting transition gets logged to the audit event store. The current M1
  table is `event_log`; `application_events` is proposed future vocabulary only.
- Open questions for later:
  - Polling cadence and per-source rate limits.
  - Dedupe of repeated/duplicate status signals.
  - Reading an ATS status page likely needs the browser worker (Playwright) -> also a phase 2 dependency, also High/Critical risk.

## 2. Failed-application detection + remediation report

_From team review: highlight jobs that weren't successfully applied, and produce a report on how to finish the application manually._

- Surface applications stuck in `FAILED` in the dashboard (review-queue filter or a dedicated "Needs manual follow-up" view).
- Auto-generate a **"finish this manually"** report per failed application:
  - Company + role + posting URL.
  - Which step failed and why - reuse the existing full-auto fallback reasons: captcha, unknown field, login required, conflicting data, low confidence.
  - The packet we already generated (CV bullets, cover note, screening answers) so a human can copy/paste rather than redo work.
  - Remaining fields / what's left to complete.
- Pull the failure reason from the executor record plus the event log - **read the audit trail,
  don't recompute it.** The current M1 table is `executor_actions`; `executor_runs` is a proposed
  future name only.
- Make it exportable/printable so a person can knock out the application by hand quickly.

## 3. Keep this doc as the running parking lot

_From team review: keep a lightweight markdown parking lot so good ideas are captured before they become real work._

- This file is the low-ceremony capture list. Bullets, not specs.
- Promote an item to a real planning ticket (`M<milestone>-APP-###`) only when we actually pick it up.

---

## Adjacent ideas worth noting while we're here

- Status-change notifications (dashboard/email) when an application moves to `INTERVIEW` or `REJECTED`.
- "Stale application" detection - `APPLIED` with no movement after N days -> nudge to follow up.
- Aggregate funnel metrics on the dashboard (discovered -> applied -> interview conversion).

## Governance guardrails to keep in mind for all of the above

- No new external side effect without a policy decision - ATS status-page reads and follow-up emails both count as side effects.
- Listeners + report generation are **read / propose only**. No state mutation outside the state machine.
- Anything touching Gmail or the browser is **High/Critical risk** -> dry-run first, plus Nicolay + Francis sign-off.
- Validate any LLM-derived status/classification before it's persisted or drives a transition.
