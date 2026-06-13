# ApplyPilot Frontend

This folder contains the milestone-1 audit dashboard scaffold.

The current implementation is dependency-free static HTML/CSS/JavaScript so the UI can be reviewed without introducing a frontend build system before the product surface stabilizes.

Open `index.html` in a browser to review the dashboard.

The dashboard can:

- Load `GET /applications/{application_id}/audit` from a running backend.
- Show local demo audit data when no application ID is provided.
- Display the application record, event log, policy decisions, and executor dry-run actions.
- Show basic loading, fallback, and empty states.

Future iterations can replace this with a framework app without changing the repository boundary.
