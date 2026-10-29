"""Translate forecasts into liquidity language. Predictions are not guarantees.

Provides an async liquidity service to load transaction history, run spend forecasting
(using SpendLSTM with baseline fallbacks), and reconcile projections against current balance.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.services.transactions import list_transactions, to_dicts
from ml.anomaly_detection.subscriptions import detect_subscriptions
from ml.forecasting.pipeline import forecast_spend

DISCLAIMER = (
    "Informational guidance only — not professional financial advice. "
    "Projected figures are model estimates, not guaranteed outcomes."
)


def liquidity_state(
    current_balance: float,
    predicted_spend: float,
    recurring_obligations: float,
    horizon_days: int,
) -> dict:
    """Reconcile projected expenditure and upcoming recurring commitments against user balance."""
    required = predicted_spend + recurring_obligations
    remaining = current_balance - required
    shortfall = max(0.0, required - current_balance)
    if shortfall > 0:
        warning = (
            f"Your projected spending (about ₹{predicted_spend:,.0f}) and upcoming recurring expenses "
            f"(about ₹{recurring_obligations:,.0f}) over the next {horizon_days} days may cause a "
            f"shortfall of approximately ₹{shortfall:,.0f}."
        )
    elif remaining < 0.15 * max(current_balance, 1):
        warning = (
            f"Projected remaining balance is approximately ₹{remaining:,.0f}. Liquidity may be tight "
            f"near the end of this horizon."
        )
    else:
        warning = (
            f"Projected remaining balance is approximately ₹{remaining:,.0f} based on the model. "
            "This is an estimate, not a guaranteed future balance."
        )
    return {
        "current_balance": round(current_balance, 2),
        "predicted_spend": round(predicted_spend, 2),
        "recurring_obligations": round(recurring_obligations, 2),
        "predicted_balance": round(remaining, 2),
        "shortfall_amount": round(shortfall, 2),
        "warning": warning,
        "disclaimer": DISCLAIMER,
    }


async def get_user_liquidity_forecast(
    db: Session,
    current_user: User,
    horizon_days: int = 30,
) -> dict[str, Any]:
    """Async service loading user transactions, computing spend forecast (SpendLSTM / baselines),

    and reconciling forward expenditure against current cash balance to detect shortfalls.
    """
    db.refresh(current_user)
    tx_rows = to_dicts(list_transactions(db, current_user.id))

    # 1. Generate expenditure projection through forecasting pipeline (SpendLSTM / baselines)
    forecast = forecast_spend(tx_rows, horizon=horizon_days)

    # 2. Extract upcoming recurring obligations
    subs = detect_subscriptions(tx_rows)
    recurring = sum(s["typical_amount"] for s in subs)

    # 3. Reconcile with current liquid balance to compute cash shortfall
    reconciliation = liquidity_state(
        current_balance=current_user.current_balance,
        predicted_spend=forecast["predicted_spend"],
        recurring_obligations=recurring,
        horizon_days=horizon_days,
    )

    return {
        "horizon_days": horizon_days,
        "predicted_spend": round(forecast["predicted_spend"], 2),
        "predicted_balance": round(reconciliation["predicted_balance"], 2),
        "shortfall_amount": round(reconciliation["shortfall_amount"], 2),
        "model_name": forecast["model_name"],
        "daily_forecast": forecast.get("daily_forecast", []),
        "baseline_predicted_spend": round(forecast.get("baseline_predicted_spend", 0.0), 2),
        "baseline_daily_forecast": forecast.get("baseline_daily_forecast", []),
        "seasonal_daily_forecast": forecast.get("seasonal_daily_forecast", []),
        "metrics": forecast.get("metrics", {}),
        "warning": reconciliation["warning"],
        "disclaimer": reconciliation["disclaimer"],
        "current_balance": round(current_user.current_balance, 2),
        "recurring_obligations": round(recurring, 2),
        "raw_forecast": forecast,
        "subs": subs,
    }
