"""
Integration test verifying the two-stage UI endpoints and authenticated API endpoints.
"""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_ui_endpoints():
    # Test GET /login
    r_login = client.get("/login")
    assert r_login.status_code == 200
    assert "FinPulse AI" in r_login.text
    assert "login-form" in r_login.text

    # Test GET /dashboard with HTML accept
    r_dashboard = client.get("/dashboard", headers={"Accept": "text/html"})
    assert r_dashboard.status_code == 200
    assert "FinPulse AI" in r_dashboard.text
    assert "forecastChart" in r_dashboard.text

    # Test GET / with HTML accept
    r_root_html = client.get("/", headers={"Accept": "text/html"})
    assert r_root_html.status_code == 200
    assert "FinPulse AI" in r_root_html.text


def test_authenticated_flow():
    # 1. Login
    r_login = client.post("/auth/login", json={"email": "demo@finpulse.ai", "password": "demo"})
    assert r_login.status_code == 200
    token = r_login.json().get("access_token")
    assert token is not None

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Users Me
    r_me = client.get("/users/me", headers=headers)
    assert r_me.status_code == 200
    assert r_me.json()["email"] == "demo@finpulse.ai"

    # 3. Forecast endpoint
    r_forecast = client.get("/forecast", headers=headers)
    assert r_forecast.status_code == 200
    forecast_data = r_forecast.json()
    assert "predicted_spend" in forecast_data
    assert len(forecast_data["daily_forecast"]) == 30
    assert "model_name" in forecast_data

    # 4. Anomalies endpoint
    r_anomalies = client.get("/anomalies", headers=headers)
    assert r_anomalies.status_code == 200
    assert "anomalies" in r_anomalies.json()

    # 5. Transactions endpoint
    r_tx = client.get("/transactions", headers=headers)
    assert r_tx.status_code == 200
    assert isinstance(r_tx.json(), list)

    # 6. Advisor chat endpoint
    r_advisor = client.post("/advisor/chat", headers=headers, json={"message": "What is my current balance?"})
    assert r_advisor.status_code == 200
    advisor_data = r_advisor.json()
    assert "reply" in advisor_data
    assert "disclaimer" in advisor_data
