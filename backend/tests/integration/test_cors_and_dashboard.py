"""Tests verifying CORS headers for frontend dashboard access."""

from __future__ import annotations

import pathlib

from fastapi.testclient import TestClient

from applypilot.main import app


client = TestClient(app)
FRONTEND_ORIGIN = "http://localhost:3000"
REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
FRONTEND_APP = REPO_ROOT / "frontend" / "app"


def _source(relative_path: str) -> str:
    return (FRONTEND_APP / relative_path).read_text(encoding="utf-8")


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


def test_disallowed_origin_does_not_receive_cors_access() -> None:
    """Unknown origins should not be treated as valid credentialed frontend callers."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://evil.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 400
    assert response.headers.get("access-control-allow-origin") is None


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
    """The dashboard includes raw job text intake for scoring and classification."""
    index_response = client.get("/ui/index.html")
    intake_source = _source("src/components/ManualIntakePanel.tsx")

    assert index_response.status_code == 200
    assert "assets/" in index_response.text
    assert "Job description" in intake_source
    assert "raw_text" in intake_source
    assert "intakeToJobCreate" in intake_source


def test_dashboard_can_prefill_sample_job_for_demo() -> None:
    """The dashboard can prefill sample job data for faster demos."""
    index_response = client.get("/ui/index.html")
    app_source = _source("src/App.tsx")
    sample_source = _source("src/domain/sampleJob.ts")

    assert index_response.status_code == 200
    assert "sampleIntakeForm" in app_source
    assert "resetDemo" in app_source
    assert "Dashboard restored to the sample review baseline." in _source("src/state/dashboardState.ts")
    assert "Backend Platform Engineer" in sample_source
    assert "ApplyGo Demo Co." in sample_source
    assert "https://jobs.lever.co/applygo/backend-platform-engineer" in sample_source
    assert "full-time remote role" in sample_source
    assert "salary range of $95,000 - $125,000" in sample_source


def test_dashboard_can_load_recent_applications() -> None:
    """The dashboard can list recent applications and load one by ID."""
    index_response = client.get("/ui/index.html")
    recent_source = _source("src/components/RecentApplicationsPanel.tsx")
    filters_source = _source("src/domain/recentFilters.ts")
    api_source = _source("src/api/client.ts")
    styles_source = _source("src/styles.css")

    assert index_response.status_code == 200
    assert "Load recent" in recent_source
    assert "Any state" in recent_source
    assert "Any recommendation" in recent_source
    assert "Search company" in recent_source
    assert "buildRecentApplicationQuery" in filters_source
    assert "URLSearchParams" in filters_source
    assert "sort_by" in filters_source
    assert "sort_dir" in filters_source
    assert "recommendation" in filters_source
    assert "company" in filters_source
    assert "/applications?" in api_source
    assert "recent-application" in styles_source
    assert "recent-filters" in styles_source


def test_dashboard_exposes_state_progression_controls() -> None:
    """The dashboard can advance applications through governed states."""
    index_response = client.get("/ui/index.html")
    app_source = _source("src/App.tsx")
    workflow_source = _source("src/domain/workflow.ts")

    assert index_response.status_code == 200
    assert "stateTransitions" in workflow_source
    assert "/applications/${applicationId}/state" in _source("src/api/client.ts")
    assert "ReadyForReview" in workflow_source
    assert "visibleStateTransitions" in workflow_source
    assert "hasSubmissionExecutorEvidence" in workflow_source
    assert "Dry-run before marking submitted." in _source("src/components/WorkflowActions.tsx")
    assert "Confirm" in app_source


def test_dashboard_exposes_demo_readiness_guards() -> None:
    """The dashboard guides reviewers through the demo order."""
    index_response = client.get("/ui/index.html")
    app_source = _source("src/App.tsx")
    workflow_source = _source("src/domain/workflow.ts")
    workflow_component = _source("src/components/WorkflowActions.tsx")
    styles_source = _source("src/styles.css")

    assert index_response.status_code == 200
    assert "workflowReadiness" in workflow_source
    assert "Score the application before evaluating policy." in workflow_component
    assert "Evaluate policy before dry-run." in workflow_component
    assert "Policy requires review before dry-run:" in workflow_source
    assert "Plan the approved follow-up action without side effects." in workflow_component
    assert "dryRunBlockReason" in workflow_source
    assert "policyDecisionDetail" in workflow_source
    assert "fit_score" in _source("src/api/types.ts")
    assert "recommendation" in _source("src/api/types.ts")
    assert "Planned steps" in _source("src/domain/packet.ts")
    assert "Side effects" in _source("src/components/EvidenceGrid.tsx")
    assert "button:disabled" in styles_source
    assert "setStatus" in app_source


def test_dashboard_renders_review_summary_readiness() -> None:
    """The dashboard shows compact review readiness from the API."""
    index_response = client.get("/ui/index.html")
    review_source = _source("src/components/ReviewReadiness.tsx")
    api_source = _source("src/api/client.ts")
    styles_source = _source("src/styles.css")

    assert index_response.status_code == 200
    assert "/applications/${applicationId}/review-summary" in api_source
    assert "Review readiness" in review_source
    assert "ready_for_policy" in review_source
    assert "ready_for_dry_run" in review_source
    assert "ready_for_submission" in review_source
    assert "readiness-item" in styles_source
    assert "badge.blocked" in styles_source
    assert ".empty-state" in styles_source


def test_dashboard_summarizes_audit_timeline_events() -> None:
    """The dashboard renders readable summaries for audit timeline events."""
    timeline_source = _source("src/components/AuditTimeline.tsx")

    assert "eventTitle" in timeline_source
    assert "eventSummary" in timeline_source
    assert "Application created" in timeline_source
    assert "Application state updated" in timeline_source
    assert "Policy decision recorded" in timeline_source
    assert "Preview result recorded" in timeline_source
    assert "Event key:" in timeline_source
    assert "State change:" in timeline_source
    assert "Policy decision:" in timeline_source
    assert "Executor result:" in timeline_source
    assert "application.scored" in timeline_source


def test_dashboard_empty_states_guide_reviewers_to_next_step() -> None:
    """Empty dashboard panels should tell reviewers what action unblocks the view."""
    evidence_source = _source("src/components/EvidenceGrid.tsx")
    recent_source = _source("src/components/RecentApplicationsPanel.tsx")
    packet_source = _source("src/components/PacketPanel.tsx")
    timeline_source = _source("src/components/AuditTimeline.tsx")
    styles_source = _source("src/styles.css")

    assert "No score recorded" in evidence_source
    assert "Run scoring to generate fit evidence" in evidence_source
    assert "No policy decisions recorded" in evidence_source
    assert "No preview actions recorded" in evidence_source
    assert "No applications loaded" in recent_source
    assert "No packet review history yet" in packet_source
    assert "No audit events recorded" in timeline_source
    assert ".empty-state" in styles_source
