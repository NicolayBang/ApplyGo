# ApplyPilot Frontend

This folder contains the milestone-1 audit dashboard scaffold.

The current implementation is dependency-free static HTML/CSS/JavaScript so the UI can be reviewed without introducing a frontend build system before the product surface stabilizes.

## Quick start (demo mode)

Open `index.html` in a browser to review the dashboard with built-in demo data.  
No backend required — the page renders a local audit trail immediately.

## End-to-end demo flow (backend → dashboard)

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
cd backend
alembic upgrade head
```

### 4. Seed demo data

```bash
cd backend
python -m applypilot.dev.demo_seed
```

This prints identifiers including an **Application ID** (UUID).

### 5. Start the backend API

```bash
cd backend
uvicorn applypilot.main:app --reload
```

The API is available at `http://localhost:8000`.  
Verify with: `curl http://localhost:8000/health`

### 6. Open the dashboard

Open `frontend/index.html` in a browser (file:// or a local HTTP server both work — CORS is enabled on the backend).

### 7. Load audit data

1. Paste the **Application ID** from step 4 into the "Application ID" field.
2. Ensure "API base" is set to `http://localhost:8000`.
3. Click **Load audit**.

The dashboard will display the application record, policy decisions, executor actions, and full audit timeline fetched from the backend.

## Manual intake

With the backend running, the dashboard can create a manual application directly:

1. Fill in role title and company.
2. Optionally add location, job URL, and remote preference.
3. Click **Create**.

The dashboard calls `POST /jobs`, then `POST /applications`, copies the new application ID into the audit controls, and loads `GET /applications/{application_id}/audit`.

## API endpoint

The dashboard fetches audit data from:

```
GET /applications/{application_id}/audit
```

Response shape:

```json
{
  "application": { "id": "...", "state": "...", ... },
  "events": [ { "event_type": "...", ... } ],
  "policy_decisions": [ { "action_type": "...", "allowed": true, ... } ],
  "executor_actions": [ { "action_type": "...", "status": "planned", ... } ]
}
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| "Failed to fetch" error | Backend not running. Start with `uvicorn applypilot.main:app --reload` |
| 404 on audit load | Application ID not found — re-run `python -m applypilot.dev.demo_seed` |
| "Invalid ID" status | Paste a full UUID (e.g. `5f2c4a50-8f75-4d38-a40f-15fd5f8f27d4`) |

## Architecture note

Future iterations can replace this with a framework app without changing the repository boundary.
