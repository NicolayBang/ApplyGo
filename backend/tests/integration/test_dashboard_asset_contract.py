"""Static dashboard asset contract tests."""

from __future__ import annotations

import re

from fastapi.testclient import TestClient

from applypilot.main import app


client = TestClient(app)


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
