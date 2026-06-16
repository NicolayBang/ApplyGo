# ApplyGo Frontend

This folder contains the milestone-1 audit dashboard scaffold.

The current implementation is dependency-free static HTML/CSS/JavaScript so the UI can be reviewed
without introducing a frontend build system before the product surface stabilizes.

## Quick start (demo mode)

Open `index.html` in a browser to review the dashboard with built-in demo data. No backend is
required; the page renders a local audit trail immediately.

For the live M1 demo, prefer serving the dashboard from the backend at `http://localhost:8000/ui/`
after the API is running. This keeps the dashboard, API base inference, and CORS behavior closest to
the reviewer flow.

## End-to-end demo flow

Follow these steps to seed real audit data and view it in the dashboard.

### 1. Start infrastructure

```bash
docker compose up -d postgres
```

### 2. Install backend dependencies

```bash
cd backend
pip install -e ".[dev]"
```

### 3. Run database migrations

```bash
alembic upgrade head
```

### 4. Seed demo data

```bash
python -m applypilot.dev.demo_seed
```

This prints identifiers including an **Application ID** UUID.

### 5. Start the backend API

```bash
uvicorn applypilot.main:app --reload
```

The API is available at `http://localhost:8000`.

Verify with:

```bash
curl http://localhost:8000/health
```

### 6. Open the dashboard

Open `http://localhost:8000/ui/` in a browser after starting the backend.

Opening `frontend/index.html` directly still works for local review, but the backend-served `/ui/`
path is the preferred manual demo route.

### 7. Load audit data

1. Paste the **Application ID** from step 4 into the "Application ID" field.
2. Ensure "API base" is set to `http://localhost:8000`.
3. Click **Load audit**.

The dashboard will display the application record, review readiness, policy decisions, executor
actions, and full audit timeline fetched from the backend.

## Application packet preview

The dashboard includes an M2 application packet preview. It is generated from the currently loaded
application, job, score, policy, executor, and next-action evidence.

The packet preview is intentionally read-only:

- it does not persist packet content;
- it does not create `documents` rows;
- it does not send email;
- it does not open browser automation;
- it does not submit an application.

Use **Copy packet** to copy the full generated packet text for manual review. Use **Copy cover
note** when the reviewer only needs the deterministic cover-note draft. Clipboard access depends on
browser permissions; if the browser denies access, the dashboard shows a non-blocking status message.

## Manual intake

With the backend running, the dashboard can create a manual application directly:

1. Click **Sample job** for the fastest M1 happy path, or fill in role title and company manually.
2. Optionally add location, job URL, remote preference, and a job description.
3. Click **Create**.

The dashboard calls `POST /jobs`, then `POST /applications`, copies the new application ID into the
audit controls, and loads `GET /applications/{application_id}/audit`.

The backend deterministically enriches blank job metadata during job creation. The application
summary can show inferred `job_type`, `ats_type`, `salary_raw`, and `remote_ok` values when the
intake data supports them.

The built-in Sample job includes enough deterministic signals for the M1 happy path: ATS source,
full-time job type, compensation range, remote marker, and detailed job text.

## Guided actions

With an application loaded, the dashboard can continue the current guided workflow:

1. Click **Score application** to record fit evidence when it is not already present.
2. Click **Evaluate policy** to call `POST /applications/{application_id}/policy-decisions`.
3. Click **Preview action** to call `POST /applications/{application_id}/executor-actions/dry-run`.
4. The audit panel reloads and shows the score, policy decision, and executor attempt/result events.

The dry-run action requires an allowed policy decision. If no allowed decision exists, the dashboard
asks for policy evaluation first.

If policy returns `review` or `deny`, the dry-run button remains disabled and the workflow hint
explains the required review or override. That is expected governed behavior, not a dashboard error.

Executor details include side-effect status, planned steps, and required safeguards so reviewers can
inspect what would happen without triggering external automation.

The application packet preview updates from the same loaded audit data. After scoring, policy, and
dry-run, the packet text includes fit evidence, governance evidence, safeguards, planned steps, and
the next human action.

The packet also includes a deterministic cover-note draft generated from the current application,
job, score, policy, and executor evidence. The draft is intended for human review only: it is not
persisted, it does not call an LLM, and it does not send external follow-up.

## API endpoint

The dashboard fetches audit and review data from:

```text
GET /applications/{application_id}/audit
GET /applications/{application_id}/review-summary
```

Response shape:

```json
{
  "application": { "id": "...", "state": "...", "...": "..." },
  "events": [{ "event_type": "...", "...": "..." }],
  "policy_decisions": [{ "action_type": "...", "allowed": true }],
  "executor_actions": [
    {
      "action_type": "...",
      "status": "planned",
      "result": {
        "side_effects": false,
        "planned_steps": [],
        "requires": []
      }
    }
  ]
}
```

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| "Failed to fetch" error | Backend not running. Start with `uvicorn applypilot.main:app --reload`. |
| 404 on audit load | Application ID not found. Re-run `python -m applypilot.dev.demo_seed`. |
| "Invalid ID" status | Paste a full UUID, for example `5f2c4a50-8f75-4d38-a40f-15fd5f8f27d4`. |

## Architecture note

Future iterations can replace this with a framework app without changing the repository boundary.
