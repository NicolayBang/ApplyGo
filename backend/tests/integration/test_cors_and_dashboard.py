"""Tests verifying CORS headers for frontend dashboard access."""

from __future__ import annotations

from fastapi.testclient import TestClient

from applypilot.main import app


client = TestClient(app)


def test_cors_headers_present_on_health_endpoint() -> None:
    """The dashboard opens from file:// or a different origin; CORS must allow it."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "*"


def test_cors_headers_present_on_audit_endpoint() -> None:
    """The dashboard fetches /applications/{id}/audit cross-origin."""
    response = client.options(
        f"/applications/{'0' * 8}-{'0' * 4}-{'0' * 4}-{'0' * 4}-{'0' * 12}/audit",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "*"
