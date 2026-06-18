# ApplyGo Frontend

The dashboard is a React + TypeScript application built with Vite.

The source lives in `frontend/app/`. Production assets are built to `frontend/dist/` and served by
FastAPI at `/ui/`.

## Quick start

```bash
cd frontend/app
npm ci
npm run dev
```

The Vite development server is for frontend iteration. The app still defaults its API base to
`http://localhost:8000` for local backend calls.

## Build for backend serving

```bash
cd frontend/app
npm ci
npm run build
```

After the build, start the backend and open:

```text
http://localhost:8000/ui/
```

The build uses Vite `base: "./"` so the generated `frontend/dist/index.html` can also be opened
directly for offline demo review.

## Quality gates

```bash
cd frontend/app
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

## Preserved workflow behavior

- Demo mode works without a backend.
- Manual intake calls `POST /jobs`, then `POST /applications`.
- Audit loading calls `GET /applications/{id}/audit` and `GET /applications/{id}/review-summary`.
- Scoring, policy evaluation, dry-run preview, state transitions, and packet reviews use the
  existing backend JSON routes.
- The packet preview and cover note are deterministic client-side text generated from current
  review evidence.
- Recording a packet review does not send email, open a browser, or submit an application.
- Dry-run requires an allowed policy decision, and submission is hidden until dry-run executor
  evidence exists.

## Design boundary

This is an operational reviewer dashboard, not a landing page. Keep future UI changes focused on
workflow clarity, audit visibility, and fast inspection of one application at a time unless a future
approved milestone introduces a new product surface.
