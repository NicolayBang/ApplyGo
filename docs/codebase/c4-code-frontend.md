# C4 Code Level: Frontend Dashboard

## Overview

- **Location**: `frontend/app/`
- **Implementation**: React, TypeScript, Vite, and TanStack Query.
- **Build output**: `frontend/dist/`
- **Serving mode**: FastAPI `/ui` serves the built Vite assets.
- **Purpose**: Demonstrate and inspect the governed workflow without changing backend contracts.

## Source Areas

| Area | Responsibility |
|---|---|
| `src/api/` | Typed API client, route calls, query/mutation hooks |
| `src/domain/` | Pure workflow, readiness, packet, label, filter, and demo-data logic |
| `src/state/` | Local reducer state for API base, selected app, filters, notes, and status |
| `src/components/` | Dashboard panels and reviewer-facing UI |
| `src/styles.css` | Visual system and responsive layout |

## Runtime Responsibilities

- Demo fixtures support offline review with no backend required.
- Manual intake creates a job and application through existing JSON routes.
- Live mode loads audit and review-summary read models from the backend.
- Workflow controls expose only valid next-state actions and keep destructive choices explicit.
- Policy evaluation must precede executor dry-run.
- Dry-run must precede the `Submitted` transition becoming available.
- Packet preview and cover note text are deterministic client-side outputs.
- Packet review records human review evidence without external side effects.
- Audit timeline remains visible for every loaded application.

## Validation

Frontend gates:

```bash
cd frontend/app
npm ci
npm run typecheck
npm run test
npm run build
```

Backend static asset tests expect `frontend/dist/` to exist:

```bash
cd frontend/app
npm run build
cd ../../backend
python -m pytest tests/integration/test_dashboard_asset_contract.py
```

## API Contract

The dashboard preserves the existing backend route shapes. Its primary read models are:

- `GET /applications/{application_id}/audit`
- `GET /applications/{application_id}/review-summary`

The audit response contains the application, ordered events, policy decisions, and executor actions.
The review-summary response contains compact readiness flags, packet review data, and guarded next
states.

## Scope

The dashboard does not perform browser automation, send email, generate documents, or submit live
applications.
