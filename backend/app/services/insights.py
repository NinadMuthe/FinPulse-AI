"""
insights.py -- Business logic service for statistical anomaly detection.

This service fetches a user's transaction history from the database, builds
the feature vector, runs it through the Isolation Forest model, and returns
enriched AnomalyResult objects.

IMPORTANT: Results represent *statistical spending anomalies* based on the
user's own historical patterns.  They are NOT indicators of banking fraud or
unauthorised access.  Users should contact their bank for security concerns.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from backend.app.models.ml_artifacts import Anomaly
from backend.app.services.transactions import list_transactions, to_dicts
from ml.anomaly_detection.isolation import TransactionAnomalyDetector, AnomalyResult

if TYPE_CHECKING:
    from backend.app.models.user import User

logger = logging.getLogger(__name__)

# Model is stateless (trained per-request on user history) so contamination
# is a module-level constant; change here to affect the whole service.
_CONTAMINATION: float = 0.08

ANOMALY_DISCLAIMER: str = (
    "These are statistical spending anomalies detected by comparing your "
    "transactions against your own historical patterns using an Isolation Forest "
    "model. They are NOT fraud alerts and do NOT imply unauthorised access to "
    "your account. Always verify unexpected transactions directly with your bank."
)


def _preprocess(rows: list[dict]) -> list[dict]:
    """
    Ensure every row has the fields the detector expects.
    Fills in safe defaults for any missing optional fields.
    """
    cleaned: list[dict] = []
    for r in rows:
        # Skip credit entries -- anomaly detection focuses on spending
        if r.get("transaction_type") == "credit":
            continue
        dt = r.get("transaction_date")
        if dt is None:
            dt = datetime.now(timezone.utc)
        # Normalise to a plain datetime so getattr(dt, 'hour') always works
        if hasattr(dt, "date") and not hasattr(dt, "hour"):
            dt = datetime.combine(dt, datetime.min.time())
        cleaned.append(
            {
                "id": r.get("id"),
                "amount": float(r.get("amount") or 0),
                "merchant": str(r.get("merchant") or "Unknown"),
                "category": str(r.get("category") or "Other"),
                "transaction_date": dt,
                "transaction_type": r.get("transaction_type", "debit"),
                "description": r.get("description", ""),
            }
        )
    return cleaned


def run_anomaly_detection(
    db: Session,
    current_user: "User",
    *,
    save_to_db: bool = True,
) -> dict:
    """
    Fetch the user's transaction history, train an Isolation Forest on the
    full history, score every transaction, and return the flagged anomalies
    along with metadata.

    Parameters
    ----------
    db : Session
        Active SQLAlchemy session (injected by FastAPI dependency).
    current_user : User
        The authenticated user whose transactions are analysed.
    save_to_db : bool
        If True (default) persist each flagged anomaly to the ``anomalies``
        table so they appear in audit queries.

    Returns
    -------
    dict with keys:
        anomalies        -- list of enriched anomaly dicts
        total_analysed   -- number of debit transactions fed into the model
        disclaimer       -- plain-English disclaimer string
        model_params     -- dict describing the model configuration used
    """
    # 1. Fetch and serialise all transactions for this user
    raw_rows: list[dict] = to_dicts(list_transactions(db, current_user.id))
    debit_rows: list[dict] = _preprocess(raw_rows)

    logger.info(
        "Anomaly detection: user_id=%s, total_debits=%d",
        current_user.id,
        len(debit_rows),
    )

    if len(debit_rows) < 8:
        logger.warning(
            "user_id=%s has only %d debit transactions; skipping model (min 8 required).",
            current_user.id,
            len(debit_rows),
        )
        return {
            "anomalies": [],
            "total_analysed": len(debit_rows),
            "disclaimer": ANOMALY_DISCLAIMER,
            "model_params": {},
            "warning": (
                "Insufficient transaction history to run anomaly detection. "
                "At least 8 debit transactions are required."
            ),
        }

    # 2. Train + score
    detector = TransactionAnomalyDetector(
        contamination=_CONTAMINATION,
        random_state=42,
    )
    detector.fit(debit_rows)
    results: list[AnomalyResult] = detector.predict(debit_rows)

    logger.info(
        "Anomaly detection: user_id=%s, flagged=%d / %d",
        current_user.id,
        len(results),
        len(debit_rows),
    )

    # 3. Optionally persist to the anomalies table for audit / history
    if save_to_db and results:
        for r in results:
            db.add(
                Anomaly(
                    user_id=current_user.id,
                    transaction_id=r.transaction_id,
                    score=r.anomaly_score,
                    reason=r.reason[:255],  # column cap
                )
            )
        try:
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("Failed to persist anomaly records to DB — continuing.")

    return {
        "anomalies": [r.to_dict() for r in results],
        "total_analysed": len(debit_rows),
        "disclaimer": ANOMALY_DISCLAIMER,
        "model_params": {
            "algorithm": "IsolationForest",
            "contamination": _CONTAMINATION,
            "random_state": 42,
            "n_estimators": 200,
            "features": [
                "amount_norm",
                "hour_of_day",
                "day_of_week",
                "z_score",
                "merchant_rarity",
            ],
        },
    }
