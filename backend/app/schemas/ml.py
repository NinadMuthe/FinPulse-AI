from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ForecastOut(BaseModel):
    horizon_days: int
    predicted_spend: float
    predicted_balance: float | None
    shortfall_amount: float
    model_name: str
    daily_forecast: list[float] = Field(default_factory=list)
    baseline_predicted_spend: float | None = None
    metrics: dict = Field(default_factory=dict)
    warning: str
    disclaimer: str


class AnomalyOut(BaseModel):
    """Enriched anomaly record returned by GET /anomalies.

    Fields
    ------
    transaction_id   -- PK of the flagged transaction (None for legacy rows)
    amount           -- transaction amount in INR
    merchant         -- merchant name
    category         -- spending category
    transaction_date -- when the transaction occurred
    anomaly_score    -- inverted Isolation Forest score; higher = more anomalous
    triggered_features -- list of feature names that exceeded their thresholds,
                          e.g. ['unusual_amount', 'rare_merchant']
    reason           -- human-readable explanation (NOT a fraud verdict)

    Note: 'score' is kept as an alias for anomaly_score for backward compat.
    """

    transaction_id: Optional[int] = None
    amount: Optional[float] = None
    merchant: Optional[str] = None
    category: Optional[str] = None
    transaction_date: Optional[datetime] = None
    # New primary score field
    anomaly_score: float = 0.0
    # Backward-compat alias (old DB-persisted rows only expose 'score')
    score: Optional[float] = None
    triggered_features: list[str] = Field(default_factory=list)
    reason: str

    model_config = {"from_attributes": True}


class DuplicateOut(BaseModel):
    left_id: int
    right_id: int
    merchant: str
    amount: float
    hours_apart: float
    reason: str


class SubscriptionOut(BaseModel):
    merchant: str
    typical_amount: float
    interval_days: int
    occurrence_count: int
    confidence: float
    last_seen: datetime | None
    insight: str


class AdvisorChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class AdvisorChatResponse(BaseModel):
    reply: str
    used_llm: bool
    disclaimer: str
    context: dict
