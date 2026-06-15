# Codespaces Demo Quickstart

**Status:** M1 reviewer demo path  
**Audience:** recruiters, instructors, and reviewers who want to run ApplyPilot without local setup

This guide starts the current M1 demo in GitHub Codespaces. It uses the implemented backend,
PostgreSQL migrations, and dashboard served by FastAPI at `/ui/`.

## What This Demo Shows

```text
manual intake -> parse/classify -> state progression -> scoring -> policy check -> dry-run executor -> review readiness -> audit timeline
```

The demo does not send email, open browser automation, call an LLM, or submit real applications.
External-action-like behavior stays in dry-run mode.

## Open In Codespaces

1. Open the ApplyPilot repository on GitHub.
2. Select **Code**.
3. Select **Codespaces**.
4. Create a Codespace on `main`.
5. Wait for setup to finish.

## Start The Demo Environment

From the repository root in the Codespaces terminal:

```bash
docker compose up -d postgres redis
docker compose run --rm migrate
cd backend
python -m pip install -e ".[dev]"
python -m uvicorn applypilot.main:app --host 0.0.0.0 --port 8000
```

Keep the backend terminal running.

## Open The Dashboard

1. In Codespaces, open the forwarded port for `8000`.
2. Add `/ui/` to the forwarded URL.
3. Confirm the dashboard loads.

You can also check the backend health endpoint:

```bash
curl -s http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok","service":"applypilot"}
```

## Run The M1 Happy Path

In the dashboard:

1. Click `Sample job`.
2. Click `Create`.
3. Move the application through:

```text
ApplicationCreated -> Draft -> ReadyForReview -> Approved
```

4. Click `Score application`.
5. Click `Evaluate policy`.
6. Click `Preview action`.
7. Review:
   - application summary;
   - score details;
   - policy decision;
   - dry-run executor result;
   - review readiness;
   - audit timeline.

## Expected Result

- The application is created and assigned an ID.
- State transitions are logged.
- Scoring records fit, confidence, recommendation, reasons, and risks.
- Policy decision is recorded before executor planning.
- Dry-run executor result shows `side_effects: false`.
- Audit timeline shows creation, state changes, scoring, policy, executor attempt, and executor
  result events.
- The dashboard does not imply real external submission.

## If Something Looks Blocked

If policy returns `review` instead of allowing dry-run, that can be correct governed behavior for
sparse or low-confidence input. Use the built-in `Sample job` path for the intended M1 happy-path
demo.

## Stop The Environment

When done:

```bash
cd /workspaces/ApplyPilot
docker compose down
```

Then stop the Codespace from the GitHub Codespaces UI to avoid unnecessary usage.

## Deeper Validation

For full DB-backed validation, use:

- `docs/devops/codespaces.md`
- `docs/capstone/dashboard-demo-flow.md`
- `docs/capstone/m1-demo-review-checklist.md`
