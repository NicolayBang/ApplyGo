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


def test_dashboard_packet_preview_contract_is_wired() -> None:
    """The dashboard exposes the M2 packet preview without adding backend routes."""
    index_response = client.get("/ui/index.html")
    style_response = client.get("/ui/styles.css")
    script_response = client.get("/ui/app.js")

    assert index_response.status_code == 200
    assert style_response.status_code == 200
    assert script_response.status_code == 200

    assert 'aria-label="Application packet preview"' in index_response.text
    assert 'id="packet-preview"' in index_response.text
    assert 'id="copy-cover-note-button"' in index_response.text
    assert 'id="copy-packet-button"' in index_response.text
    assert "buildPacketPreview" in script_response.text
    assert "buildCoverNoteDraft" in script_response.text
    assert "Deterministic cover-note draft copied to clipboard." in script_response.text
    assert "Deterministic Cover Note Draft" in script_response.text
    assert "renderPacketPreview" in script_response.text
    assert "Preview only. No email, browser automation, external submission" in script_response.text
    assert ".packet-panel" in style_response.text
    assert ".packet-preview" in style_response.text


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
