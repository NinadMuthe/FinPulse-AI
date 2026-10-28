"""Translate forecasts into liquidity language. Predictions are not guarantees."""

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
