# C4 Code Level: Applications Domain

## Overview

- **Location**: `backend/src/applypilot/domain/applications/`
- **Purpose**: Define API data shapes, deterministic intake classification, and scoring.
- **External AI use**: None in Milestone 1.

## API Models

### Jobs

`JobCreate` accepts optional source URL, raw text, title, company, location, job type, ATS
type, and salary text plus `remote_ok`. `JobRead` adds UUID and timestamps.

### Applications

`ApplicationCreate` requires `job_id` and defaults `automation_mode` to `manual`.
`ApplicationRead` exposes the linked job, workflow state, automation mode, score evidence,
and timestamps.

`ApplicationStateUpdate` carries a target `ApplicationState`, actor, and optional payload.
`ApplicationScoreRequest` carries the scoring actor.

### Audit

`EventLogRead` represents one append-only event. `ApplicationAuditRead` combines an
application with its events, policy decisions, and executor actions.

## `JobIntakeClassifier`

`classify()` derives:

- job type from deterministic text markers
- ATS type from known URL domains or text markers
- salary text from labelled or currency patterns
- remote compatibility from location and text

`enrich()` fills only blank fields and preserves human-provided classifications.

Known ATS classifications include Ashby, Greenhouse, Lever, LinkedIn, Workday, and
SmartRecruiters.

## `ApplicationScorer`

### `JobScoringInput`

Immutable normalized input containing the job fields used by scoring.

### `score()`

Starts at 40 points and adds evidence for title, company, source URL, detailed description,
remote compatibility, job type, salary information, and relevant technical keywords.
The result is clamped to 0-100.

The scorer also records:

- missing data for absent review inputs
- a human-review risk for senior or lead expectations
- a red flag for unpaid or commission-only compensation

### Result Classification

- Confidence is low for red flags, scores below 50, or at least three missing fields.
- Confidence is high for scores of at least 75 with no missing data.
- Other results have medium confidence.
- Recommendation is `not_recommended` for red flags or scores below 45.
- Recommendation is `recommended` for scores of at least 75.
- Other results are `needs_review`.

## Persistence

The Tracker stores score, confidence, recommendation, reasons, risks, missing data, and red
flags on the canonical application and appends an `application.scored` event.
