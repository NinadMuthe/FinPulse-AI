"""
tests/test_root.py — Phase 1 backend foundation tests.

Tests:
- GET /         → 200, correct project name
- GET /health   → 200, status == "healthy"
- GET /docs     → 200 (Swagger UI is served)
"""

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_root_returns_200() -> None:
    """Root endpoint should return HTTP 200."""
    response = client.get("/")
    assert response.status_code == 200


def test_root_contains_project_name() -> None:
    """Root response should contain the project identifier."""
    response = client.get("/")
    body = response.json()
    assert "FinPulse AI" in body.get("project", "")


def test_root_has_version() -> None:
    """Root response should include a version string."""
    response = client.get("/")
    body = response.json()
    assert "version" in body
    assert body["version"]  # not empty


def test_health_returns_200() -> None:
    """Health endpoint should return HTTP 200."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_status_is_healthy() -> None:
    """Health endpoint should report status as 'healthy'."""
    response = client.get("/health")
    body = response.json()
    assert body.get("status") == "healthy"


def test_docs_endpoint_returns_200() -> None:
    """Swagger UI (/docs) should be accessible."""
    response = client.get("/docs")
    assert response.status_code == 200
