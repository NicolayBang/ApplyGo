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


def test_dashboard_can_prefill_sample_job_for_demo() -> None:
    """The static dashboard can prefill sample job data for faster demos."""
    index_response = client.get("/ui/index.html")
    script_response = client.get("/ui/app.js")

    assert index_response.status_code == 200
    assert script_response.status_code == 200
    assert 'id="sample-job-button"' in index_response.text
    assert "sampleJob" in script_response.text
    assert "loadSampleJob" in script_response.text
    assert "Backend Platform Engineer" in script_response.text
    assert "ApplyGo Demo Co." in script_response.text
    assert "https://jobs.lever.co/applygo/backend-platform-engineer" in script_response.text
    assert "full-time remote role" in script_response.text
    assert "salary range of $95,000 - $125,000" in script_response.text


def test_dashboard_can_load_recent_applications() -> None:
    """The static dashboard can list recent applications and load one by ID."""
    index_response = client.get("/ui/index.html")
    style_response = client.get("/ui/styles.css")
    script_response = client.get("/ui/app.js")

    assert index_response.status_code == 200
    assert style_response.status_code == 200
    assert script_response.status_code == 200
    assert 'id="recent-applications-button"' in index_response.text
    assert 'id="recent-filters-form"' in index_response.text
    assert 'id="recent-state-filter"' in index_response.text
    assert 'id="recent-recommendation-filter"' in index_response.text
    assert 'id="recent-company-filter"' in index_response.text
    assert 'id="recent-sort-filter"' in index_response.text
    assert 'id="recent-applications-list"' in index_response.text
    assert "loadRecentApplications" in script_response.text
    assert "recentApplicationQuery" in script_response.text
    assert "URLSearchParams" in script_response.text
    assert "sort_by" in script_response.text
    assert "sort_dir" in script_response.text
    assert "recommendation" in script_response.text
    assert "company" in script_response.text
    assert "data-application-id" in script_response.text
    assert "recent-application" in style_response.text
    assert "recent-filters" in style_response.text


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
    assert "visibleStateTransitions" in script_response.text
    assert "hasSubmissionExecutorEvidence" in script_response.text
    assert "Dry-run before marking submitted." in script_response.text
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
    assert "setActionMetadata" in script_response.text
    assert "Create or load an application before scoring." in script_response.text
    assert "Create or load an application before policy evaluation." in script_response.text
    assert "Score the application to generate reviewer evidence." in script_response.text
    assert "Evaluate whether policy allows the dry-run preview." in script_response.text
    assert "Score the application before evaluating policy." in script_response.text
    assert "Evaluate policy before dry-run." in script_response.text
    assert "Policy requires review before dry-run:" in script_response.text
    assert "Create or load an application before dry-run." in script_response.text
    assert "Plan the approved follow-up action without side effects." in script_response.text
    assert "dryRunBlockReason" in script_response.text
    assert "policyDecisionDetail" in script_response.text
    assert "fit_score" in script_response.text
    assert "recommendation" in script_response.text
    assert "compactMeta" in script_response.text
    assert "Required overrides" in script_response.text
    assert "Planned steps" in script_response.text
    assert "Side effects" in script_response.text
    assert "button:disabled" in style_response.text
    assert "clearStateActions" in script_response.text
    assert "focusLatestTimelineEvent" in script_response.text
    assert 'loadAudit({ focusTimeline: true })' in script_response.text
    assert "scrollIntoView" in script_response.text


def test_dashboard_renders_review_summary_readiness() -> None:
    """The static dashboard shows compact review readiness from the API."""
    index_response = client.get("/ui/index.html")
    style_response = client.get("/ui/styles.css")
    script_response = client.get("/ui/app.js")

    assert index_response.status_code == 200
    assert style_response.status_code == 200
    assert script_response.status_code == 200
    assert 'id="review-summary"' in index_response.text
    assert 'id="review-summary-status"' in index_response.text
    assert "/applications/${applicationId}/review-summary" in script_response.text
    assert "renderReviewSummary" in script_response.text
    assert "ready_for_policy" in script_response.text
    assert "ready_for_dry_run" in script_response.text
    assert "ready_for_submission" in script_response.text
    assert "readiness-item" in style_response.text
    assert "badge.blocked" in style_response.text


def test_dashboard_summarizes_audit_timeline_events() -> None:
    """The static dashboard renders readable summaries for audit timeline events."""
    script_response = client.get("/ui/app.js")

    assert script_response.status_code == 200
    assert "eventSummary" in script_response.text
    assert "State change:" in script_response.text
    assert "Policy decision:" in script_response.text
    assert "Executor result:" in script_response.text
    assert "application.scored" in script_response.text
