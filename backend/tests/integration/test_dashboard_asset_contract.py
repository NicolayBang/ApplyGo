"""Static dashboard asset contract tests."""

from __future__ import annotations

import pathlib

from fastapi.testclient import TestClient

from applypilot.main import app


client = TestClient(app)
REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
FRONTEND_APP = REPO_ROOT / "frontend" / "app"
FRONTEND_DIST = REPO_ROOT / "frontend" / "dist"
EXPECTED_DASHBOARD_API_PATHS = {
    "/jobs",
    "/applications",
    "/applications/${applicationId}/state",
    "/applications/${applicationId}/score",
    "/applications/${applicationId}/packet-reviews",
    "/applications/${applicationId}/policy-decisions",
    "/applications/${applicationId}/executor-actions/dry-run",
    "/applications/${applicationId}/audit",
    "/applications/${applicationId}/review-summary",
}


def _read_source(relative_path: str) -> str:
    return (FRONTEND_APP / relative_path).read_text(encoding="utf-8")


def test_built_dashboard_is_served_from_ui_route() -> None:
    """The backend serves the Vite build artifact at /ui/."""
    assert FRONTEND_DIST.exists(), "Run `npm run build` in frontend/app before backend tests."

    response = client.get("/ui/")

    assert response.status_code == 200
    assert '<div id="root"></div>' in response.text
    assert "assets/" in response.text


def test_dashboard_api_client_uses_supported_routes() -> None:
    """Every dashboard API path stays inside the supported route contract."""
    client_source = _read_source("src/api/client.ts")

    for path in EXPECTED_DASHBOARD_API_PATHS:
        assert path in client_source


def test_dashboard_preserves_review_packet_and_timeline_surfaces() -> None:
    """The React dashboard keeps reviewer readiness, packet preview, and audit timeline visible."""
    app_source = _read_source("src/App.tsx")
    packet_source = _read_source("src/components/PacketPanel.tsx")
    timeline_source = _read_source("src/components/AuditTimeline.tsx")
    domain_source = _read_source("src/domain/packet.ts")

    assert "ReviewReadiness" in app_source
    assert "PacketPanel" in app_source
    assert "AuditTimeline" in app_source
    assert "Application packet" in packet_source
    assert "Human packet review" in packet_source
    assert "Audit timeline" in timeline_source
    assert "Deterministic Cover Note Draft" in domain_source
    assert "Preview generation only" in domain_source


def test_dashboard_preserves_governed_workflow_gates() -> None:
    """Workflow controls must keep policy, dry-run, state, and submission gates explicit."""
    app_source = _read_source("src/App.tsx")
    workflow_source = _read_source("src/domain/workflow.ts")

    assert "latestAllowedPolicyDecision" in app_source
    assert "policyContextFromApplication" in app_source
    assert "executor-actions/dry-run" in _read_source("src/api/client.ts")
    assert "hasSubmissionExecutorEvidence" in workflow_source
    assert 'transition.state !== "Submitted" || hasSubmissionExecutorEvidence' in workflow_source
    assert "dryRunBlockReason" in workflow_source


def test_dashboard_keeps_human_friendly_labels_and_filter_options() -> None:
    """Reviewer-facing text should stay readable rather than exposing raw enum names."""
    labels_source = _read_source("src/domain/labels.ts")
    recent_source = _read_source("src/components/RecentApplicationsPanel.tsx")

    assert 'ApplicationCreated: "Created"' in labels_source
    assert 'ReadyForReview: "Ready for review"' in labels_source
    assert 'needs_review: "Needs review"' in labels_source
    assert '<option value="ApplicationCreated">Created</option>' in recent_source
    assert '<option value="ReadyForReview">Ready for review</option>' in recent_source
