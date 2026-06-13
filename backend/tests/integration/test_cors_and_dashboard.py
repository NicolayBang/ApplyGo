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
