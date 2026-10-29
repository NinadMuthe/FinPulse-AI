from collections import Counter
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.ml_artifacts import Anomaly, Forecast, Subscription
from backend.app.models.user import User
from backend.app.schemas.ml import (
    AdvisorChatRequest,
    AdvisorChatResponse,
    AnomalyOut,
    DuplicateOut,
    ForecastOut,
    SubscriptionOut,
)
from backend.app.services.advisor import build_system_context, llm_reply
from backend.app.services.insights import run_anomaly_detection
from backend.app.services.liquidity import (
    DISCLAIMER,
    get_user_liquidity_forecast,
    liquidity_state,
)
from backend.app.services.transactions import list_transactions, to_dicts
from backend.app.utils.deps import get_current_user
from ml.anomaly_detection.duplicates import find_duplicates
from ml.anomaly_detection.isolation import detect_anomalies
from ml.anomaly_detection.subscriptions import detect_subscriptions
from ml.forecasting.pipeline import forecast_spend

router_forecast = APIRouter(prefix="/forecast", tags=["Forecast"])
router_anomalies = APIRouter(prefix="/anomalies", tags=["Anomalies"])
router_subscriptions = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])
router_advisor = APIRouter(prefix="/advisor", tags=["Advisor"])
router_dashboard = APIRouter(prefix="/dashboard", tags=["Dashboard"])

_STATIC_INDEX = Path(__file__).resolve().parent.parent / "static" / "index.html"
_STATIC_DASHBOARD = Path(__file__).resolve().parent.parent / "static" / "dashboard.html"


def _insight_bundle(db: Session, current: User) -> dict:
    db.refresh(current)
    rows = to_dicts(list_transactions(db, current.id))
    forecast = forecast_spend(rows, horizon=30)
    subs = detect_subscriptions(rows)
    recurring = sum(s["typical_amount"] for s in subs)
    liquidity = liquidity_state(current.current_balance, forecast["predicted_spend"], recurring, 30)
    anomalies = detect_anomalies(rows)
    duplicates = find_duplicates(rows)
    categories = Counter(r["category"] for r in rows if r["transaction_type"] == "debit")
    top_category = categories.most_common(1)[0][0] if categories else "Other"
    return {
        "rows": rows,
        "forecast": forecast,
        "subs": subs,
        "liquidity": liquidity,
        "anomalies": anomalies,
        "duplicates": duplicates,
        "top_category": top_category,
    }


@router_forecast.get("", response_model=ForecastOut)
async def get_forecast(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> ForecastOut:
    """GET /forecast

    Asynchronously generates a 30-day forward-looking expenditure projection (via SpendLSTM / baselines),
    baseline comparisons, and reconciles against the user's liquid cash balance to flag cash shortfalls.
    Secured with existing JWT dependencies.
    """
    forecast_data = await get_user_liquidity_forecast(db, current, horizon_days=30)

    record = Forecast(
        user_id=current.id,
        horizon_days=forecast_data["horizon_days"],
        predicted_spend=forecast_data["predicted_spend"],
        predicted_balance=forecast_data["predicted_balance"],
        shortfall_amount=forecast_data["shortfall_amount"],
        model_name=forecast_data["model_name"],
        metrics_json=str(forecast_data["metrics"]),
    )
    db.add(record)
    db.commit()

    return ForecastOut(
        horizon_days=forecast_data["horizon_days"],
        predicted_spend=forecast_data["predicted_spend"],
        predicted_balance=forecast_data["predicted_balance"],
        shortfall_amount=forecast_data["shortfall_amount"],
        model_name=forecast_data["model_name"],
        daily_forecast=forecast_data.get("daily_forecast", []),
        baseline_predicted_spend=forecast_data.get("baseline_predicted_spend"),
        baseline_daily_forecast=forecast_data.get("baseline_daily_forecast", []),
        metrics=forecast_data.get("metrics", {}),
        warning=forecast_data["warning"],
        disclaimer=forecast_data["disclaimer"],
    )


@router_anomalies.get("", response_model=dict)
def get_anomalies(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> dict:
    """GET /anomalies

    Runs an Isolation Forest model trained on the authenticated user's
    historical debit transactions and returns flagged statistical outliers.
    """
    result = run_anomaly_detection(db, current, save_to_db=True)
    # Coerce each anomaly dict into the enriched AnomalyOut schema
    result["anomalies"] = [
        AnomalyOut(**item).model_dump(mode="json", exclude_none=False)
        for item in result["anomalies"]
    ]
    return result


@router_anomalies.get("/duplicates", response_model=list[DuplicateOut])
def get_duplicates(db: Session = Depends(get_db), current: User = Depends(get_current_user)) -> list[DuplicateOut]:
    bundle = _insight_bundle(db, current)
    return [DuplicateOut(**item) for item in bundle["duplicates"]]


@router_subscriptions.get("", response_model=list[SubscriptionOut])
def get_subscriptions(db: Session = Depends(get_db), current: User = Depends(get_current_user)) -> list[SubscriptionOut]:
    bundle = _insight_bundle(db, current)
    out = []
    for item in bundle["subs"]:
        db.add(
            Subscription(
                user_id=current.id,
                merchant=item["merchant"],
                typical_amount=item["typical_amount"],
                interval_days=item["interval_days"],
                occurrence_count=item["occurrence_count"],
                confidence=item["confidence"],
                last_seen=item["last_seen"],
                notes=item["insight"],
            )
        )
        out.append(SubscriptionOut(**item))
    db.commit()
    return out


@router_advisor.post("/chat", response_model=AdvisorChatResponse)
def advisor_chat(
    payload: AdvisorChatRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> AdvisorChatResponse:
    bundle = _insight_bundle(db, current)
    context = build_system_context(
        {
            "predicted_spend": bundle["forecast"]["predicted_spend"],
            "current_balance": current.current_balance,
            "recurring_obligations": bundle["liquidity"]["recurring_obligations"],
            "shortfall_amount": bundle["liquidity"]["shortfall_amount"],
            "top_category": bundle["top_category"],
            "anomaly_count": len(bundle["anomalies"]),
            "recent_transactions": bundle["rows"][:8],
        }
    )
    reply, used_llm = llm_reply(payload.message, context)
    from backend.app.models.ml_artifacts import AdvisoryMessage

    db.add(AdvisoryMessage(user_id=current.id, role="user", content=payload.message))
    db.add(AdvisoryMessage(user_id=current.id, role="assistant", content=reply))
    db.commit()
    return AdvisorChatResponse(reply=reply, used_llm=used_llm, disclaimer=DISCLAIMER, context=context)


@router_dashboard.get("")
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        if _STATIC_DASHBOARD.exists():
            return FileResponse(_STATIC_DASHBOARD)
        elif _STATIC_INDEX.exists():
            return FileResponse(_STATIC_INDEX)

    bundle = _insight_bundle(db, current)
    month_spend = sum(
        r["amount"]
        for r in bundle["rows"]
        if r["transaction_type"] == "debit"
    )
    return {
        "current_balance": current.current_balance,
        "current_month_spending": round(month_spend, 2),
        "forecasted_spending": bundle["forecast"]["predicted_spend"],
        "upcoming_recurring_expenses": bundle["liquidity"]["recurring_obligations"],
        "potential_anomalies": len(bundle["anomalies"]),
        "likely_duplicates": len(bundle["duplicates"]),
        "liquidity_warning": bundle["liquidity"]["warning"],
        "top_category": bundle["top_category"],
        "disclaimer": DISCLAIMER,
    }
