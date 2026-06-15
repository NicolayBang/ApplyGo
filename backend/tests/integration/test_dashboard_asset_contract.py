"""Static dashboard asset contract tests."""

from __future__ import annotations

import re

from fastapi.testclient import TestClient

from applypilot.main import app


client = TestClient(app)
EXPECTED_DASHBOARD_API_PATHS = {
    "/jobs",
    "/applications",
    "/applications/{application_id}/state",
    "/applications/{application_id}/score",
    "/applications/{application_id}/policy-decisions",
    "/applications/{application_id}/executor-actions/dry-run",
    "/applications/{application_id}/audit",
    "/applications/{application_id}/review-summary",
}


def _assert_fetch_method(script: str, path: str, method: str) -> None:
    pattern = rf"fetchJson\(`\$\{{base\}}{re.escape(path)}`,\s*\{{\s*method: \"{method}\""
    assert re.search(pattern, script, flags=re.DOTALL)


def test_dashboard_script_selectors_exist_in_markup() -> None:
    """Every id selected by app.js must exist in the dashboard HTML."""
    index_response = client.get("/ui/index.html")
    script_response = client.get("/ui/app.js")

    assert index_response.status_code == 200
    assert script_response.status_code == 200

    markup_ids = set(re.findall(r'\bid="([^"]+)"', index_response.text))
    selector_ids = set(re.findall(r'document\.querySelector\("#([^"]+)"\)', script_response.text))

    assert selector_ids
    assert selector_ids <= markup_ids


def test_dashboard_review_summary_contract_is_wired() -> None:
    """The review readiness panel has markup, script, and style coverage."""
    index_response = client.get("/ui/index.html")
    style_response = client.get("/ui/styles.css")
    script_response = client.get("/ui/app.js")

    assert index_response.status_code == 200
    assert style_response.status_code == 200
    assert script_response.status_code == 200

    assert 'aria-label="Review readiness"' in index_response.text
    assert 'id="review-summary"' in index_response.text
    assert "renderReviewSummary" in script_response.text
    assert "/review-summary" in script_response.text
    assert ".readiness-list" in style_response.text
    assert ".readiness-item" in style_response.text


def test_dashboard_guided_workflow_ui_contract_is_wired() -> None:
    """The MVP dashboard exposes the guided workflow affordances from PR #115."""
    index_response = client.get("/ui/index.html")
    style_response = client.get("/ui/styles.css")
    script_response = client.get("/ui/app.js")

    assert index_response.status_code == 200
    assert style_response.status_code == 200
    assert script_response.status_code == 200

    markup = index_response.text
    styles = style_response.text
    script = script_response.text

    assert 'id="next-action-status"' in markup
    assert 'id="next-action-title"' in markup
    assert 'id="next-action-detail"' in markup
    assert 'id="lifecycle-stepper"' in markup
    assert "Next action" in markup
    assert "Application, fit, policy, and preview" in markup

    assert "renderNextAction" in script
    assert "renderLifecycleStepper" in script
    assert "workflowReadiness" in script
    assert "Preview action" in script
    assert "Dry-run plans the approved follow-up" in script
    assert "Submission is available only after approved policy and executor preview evidence." in script
    assert "side_effects ? \"yes\" : \"no\"" in script
    assert " - dry-run only" in script

    assert ".next-action-panel" in styles
    assert ".lifecycle-stepper" in styles
    assert ".score-hero" in styles
    assert ".side-effect-banner.safe" in styles


def test_dashboard_preserves_applypilot_m1_branding_until_rename_is_explicit() -> None:
    """Frontend polish must not silently rename the implemented product."""
    index_response = client.get("/ui/index.html")
    script_response = client.get("/ui/app.js")

    assert index_response.status_code == 200
    assert script_response.status_code == 200
    assert "ApplyPilot" in index_response.text
    assert "ApplyPilot Demo Co." in script_response.text
    assert "ApplyGo" not in index_response.text
    assert "ApplyGo" not in script_response.text


def test_dashboard_fetch_paths_are_backed_by_api_routes() -> None:
    """Every dashboard API path stays inside the supported M1 route contract."""
    script_response = client.get("/ui/app.js")

    assert script_response.status_code == 200

    fetch_paths = {
        path.replace("${applicationId}", "{application_id}")
        for path in re.findall(r"fetchJson\(`\$\{base\}([^`?]+)", script_response.text)
    }

    assert fetch_paths == EXPECTED_DASHBOARD_API_PATHS


def test_dashboard_fetch_methods_match_m1_route_contract() -> None:
    """Dashboard writes use the intended route methods and reads stay implicit GETs."""
    script_response = client.get("/ui/app.js")

    assert script_response.status_code == 200

    script = script_response.text
    _assert_fetch_method(script, "/jobs", "POST")
    _assert_fetch_method(script, "/applications", "POST")
    _assert_fetch_method(script, "/applications/${applicationId}/state", "PATCH")
    _assert_fetch_method(script, "/applications/${applicationId}/score", "POST")
    _assert_fetch_method(script, "/applications/${applicationId}/policy-decisions", "POST")
    _assert_fetch_method(script, "/applications/${applicationId}/executor-actions/dry-run", "POST")
    assert "fetchJson(`${base}/applications?${recentApplicationQuery()}`)" in script
    assert "fetchJson(`${base}/applications/${applicationId}/audit`)" in script
    assert "fetchJson(`${base}/applications/${applicationId}/review-summary`)" in script
