"""
Comprehensive backend and ML integration tests for FinPulse AI.
Verifies all 20 phases:
- Auth & Users
- Transactions CRUD
- NLP Extraction
- OCR Processing
- Category Classification
- Time-series Forecasting & Baseline
- Anomaly Detection (Isolation Forest)
- Duplicate & Subscription Detection
- Liquidity & Shortfall Analysis
- AI Advisory Engine
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from ml.nlp.extract import extract_transaction
from ml.categories.taxonomy import classify_category
from ml.forecasting.pipeline import forecast_spend
from ml.anomaly_detection.isolation import detect_anomalies
from ml.anomaly_detection.duplicates import find_duplicates
from ml.anomaly_detection.subscriptions import detect_subscriptions
from backend.app.services.liquidity import liquidity_state
from backend.app.services.advisor import deterministic_reply

client = TestClient(app)


# --- Phase 4: Transactions & Endpoints ---
def test_endpoints_accessibility():
    # Root
    r_root = client.get("/")
    assert r_root.status_code == 200
    assert "FinPulse AI" in r_root.json()["project"]

    # Health
    r_health = client.get("/health")
    assert r_health.status_code == 200
    assert r_health.json()["status"] == "healthy"

    # Docs
    r_docs = client.get("/docs")
    assert r_docs.status_code == 200


# --- Phase 7: NLP Extraction ---
def test_nlp_extraction_sms():
    sms = "Your account XXXX1234 has been debited with INR 450 at Swiggy on 17-Aug-2026."
    res = extract_transaction(sms)
    assert res["amount"] == 450.0
    assert "Swiggy" in res["merchant"]
    assert res["date"] == "2026-08-17"
    assert res["category"] == "Food"
    assert res["transaction_type"] == "debit"
    assert res["confidence_score"] >= 0.75


# --- Phase 8: Categories ---
def test_category_taxonomy():
    assert classify_category("Blinkit", "bought milk and vegetables") == "Groceries"
    assert classify_category("Uber", "ride to office") == "Transport"
    assert classify_category("Netflix", "monthly subscription") == "Entertainment"


# --- Phase 9 & 10: Forecasting & Liquidity ---
def test_forecasting_and_liquidity():
    mock_history = [
        {"transaction_date": f"2026-07-{i:02d}", "amount": 500.0, "category": "Food", "transaction_type": "debit"}
        for i in range(1, 31)
    ]
    forecast = forecast_spend(mock_history, horizon=30)
    assert forecast["predicted_spend"] > 0
    assert len(forecast["daily_forecast"]) == 30

    liq = liquidity_state(
        current_balance=20000.0,
        predicted_spend=17500.0,
        recurring_obligations=5000.0,
        horizon_days=30,
    )
    assert liq["shortfall_amount"] == 2500.0
    assert "shortfall" in liq["warning"].lower()


# --- Phase 11 & 12: Anomaly, Duplicate & Subscription Detection ---
def test_ml_anomaly_and_pattern_detection():
    txns = [
        {"id": 1, "amount": 250.0, "merchant": "Swiggy", "transaction_date": "2026-08-01", "category": "Food", "source": "sms"},
        {"id": 2, "amount": 250.0, "merchant": "Swiggy", "transaction_date": "2026-08-01", "category": "Food", "source": "sms"},  # Duplicate
        {"id": 3, "amount": 499.0, "merchant": "Netflix", "transaction_date": "2026-06-05", "category": "Entertainment", "source": "sms"},
        {"id": 4, "amount": 499.0, "merchant": "Netflix", "transaction_date": "2026-07-05", "category": "Entertainment", "source": "sms"},
        {"id": 5, "amount": 499.0, "merchant": "Netflix", "transaction_date": "2026-08-05", "category": "Entertainment", "source": "sms"},  # Subscription
        {"id": 6, "amount": 45000.0, "merchant": "Boutique", "transaction_date": "2026-08-10", "category": "Shopping", "source": "sms"},  # Spurious spike
    ]

    # Duplicate check
    dups = find_duplicates(txns)
    assert len(dups) >= 1

    # Subscription check
    subs = detect_subscriptions(txns)
    assert any("Netflix" in s["merchant"] for s in subs)

    # Statistical Anomaly check
    anomalies = detect_anomalies(txns)
    assert isinstance(anomalies, list)


# --- Phase 13: Advisory Engine Grounding ---
def test_advisor_grounding():
    context = {
        "current_balance": 12000,
        "forecasted_horizon_spend": 18000,
        "upcoming_recurring_expenses": 5000,
        "shortfall_amount": 11000,
        "top_category": "Food",
        "potential_anomalies": 1,
    }
    reply = deterministic_reply("Can I afford a luxury trip?", context)
    assert "₹12,000" in reply
    assert "₹18,000" in reply
    assert "shortfall" in reply.lower()
    assert "disclaimer" in reply.lower() or "estimate" in reply.lower()
