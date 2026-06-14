"""Tests verifying CORS headers for frontend dashboard access."""

from __future__ import annotations

from fastapi.testclient import TestClient

from applypilot.main import app


client = TestClient(app)
FRONTEND_ORIGIN = "http://localhost:3000"


def test_cors_headers_present_on_health_endpoint() -> None:
    """Credentialed CORS echoes the dashboard origin for preflight requests."""
    response = client.options(
        "/health",
        headers={
            "Origin": FRONTEND_ORIGIN,
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == FRONTEND_ORIGIN
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_headers_present_on_audit_endpoint() -> None:
    """The dashboard can fetch /applications/{id}/audit cross-origin."""
    response = client.options(
        f"/applications/{'0' * 8}-{'0' * 4}-{'0' * 4}-{'0' * 4}-{'0' * 12}/audit",
        headers={
            "Origin": FRONTEND_ORIGIN,
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == FRONTEND_ORIGIN
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_dashboard_manual_intake_collects_job_description() -> None:
    """The static dashboard includes raw job text intake for scoring and classification."""
    index_response = client.get("/ui/index.html")
    script_response = client.get("/ui/app.js")

    assert index_response.status_code == 200
    assert script_response.status_code == 200
    assert 'id="job-description"' in index_response.text
    assert "jobDescription" in script_response.text
    assert "raw_text" in script_response.text
    assert "job_type" in script_response.text
    assert "ats_type" in script_response.text
    assert "salary_raw" in script_response.text


def test_dashboard_exposes_state_progression_controls() -> None:
    """The static dashboard can advance applications through governed states."""
    index_response = client.get("/ui/index.html")
    script_response = client.get("/ui/app.js")

    assert index_response.status_code == 200
    assert script_response.status_code == 200
    assert 'id="state-actions"' in index_response.text
    assert "stateTransitions" in script_response.text
    assert "/applications/${applicationId}/state" in script_response.text
    assert "ReadyForReview" in script_response.text
    assert "Next states" in script_response.text


def test_dashboard_exposes_demo_readiness_guards() -> None:
    """The static dashboard guides reviewers through the demo order."""
    index_response = client.get("/ui/index.html")
    style_response = client.get("/ui/styles.css")
    script_response = client.get("/ui/app.js")

    assert index_response.status_code == 200
    assert style_response.status_code == 200
    assert script_response.status_code == 200
    assert 'id="workflow-hint"' in index_response.text
    assert "updateWorkflowReadiness" in script_response.text
    assert "Score the application before evaluating policy." in script_response.text
    assert "Evaluate policy before dry-run." in script_response.text
    assert "fit_score" in script_response.text
    assert "recommendation" in script_response.text
    assert "compactMeta" in script_response.text
    assert "Required overrides" in script_response.text
    assert "Planned steps" in script_response.text
    assert "Side effects" in script_response.text
    assert "button:disabled" in style_response.text
    assert "clearStateActions" in script_response.text


def test_dashboard_summarizes_audit_timeline_events() -> None:
    """The static dashboard renders readable summaries for audit timeline events."""
    script_response = client.get("/ui/app.js")

    assert script_response.status_code == 200
    assert "eventSummary" in script_response.text
    assert "State change:" in script_response.text
    assert "Policy decision:" in script_response.text
    assert "Executor result:" in script_response.text
    assert "application.scored" in script_response.text
