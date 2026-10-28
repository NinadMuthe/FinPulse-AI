"""
isolation.py -- Statistical spending anomaly detection using Isolation Forest.

WARNING / DISCLAIMER
This module identifies *statistically unusual* transactions based on your own
historical spending patterns.  It is NOT a fraud-detection or banking-security
system and does NOT guarantee that any flagged transaction is fraudulent or
unauthorised.  Always verify directly with your bank for any security concern.

Feature vector (5 dimensions):
    [0] amount_norm     -- amount normalised to [0, 1] across the user history
    [1] hour            -- hour of day (0-23) extracted from transaction_date
    [2] weekday         -- day of week (0 = Monday ... 6 = Sunday)
    [3] z_score         -- (amount - mean) / std  (standard-deviation distance)
    [4] merchant_rarity -- 1 / frequency of this merchant (rare = high value)
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from sklearn.ensemble import IsolationForest

# Minimum number of transactions required to train the model reliably.
_MIN_SAMPLES: int = 8

# Per-feature heuristic thresholds used to build the human-readable reason.
_AMOUNT_ZSCORE_THRESHOLD: float = 2.0   # flag when |z| > 2 standard deviations
_RARITY_THRESHOLD: float = 0.5          # flag when merchant seen < 2x in history
_UNUSUAL_HOURS: set = set(range(0, 6))  # midnight to 05:59 considered unusual


@dataclass
class AnomalyResult:
    """Rich, serialisable result object for a single flagged transaction."""

    transaction_id: Optional[int]
    amount: float
    merchant: str
    category: str
    transaction_date: object            # datetime, preserved as-is from the DB row
    anomaly_score: float                # inverted decision score: higher = more anomalous
    triggered_features: list[str] = field(default_factory=list)
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "transaction_id": self.transaction_id,
            "amount": self.amount,
            "merchant": self.merchant,
            "category": self.category,
            "transaction_date": self.transaction_date,
            "anomaly_score": round(self.anomaly_score, 4),
            "triggered_features": self.triggered_features,
            "reason": self.reason,
        }


class TransactionAnomalyDetector:
    """
    Wraps sklearn IsolationForest with finance-specific feature engineering
    and human-readable per-feature reason generation.

    Parameters
    ----------
    contamination : float
        Expected proportion of anomalous transactions (default 0.08 = 8 %).
    random_state : int
        Seed for reproducibility (default 42).
    """

    def __init__(self, contamination: float = 0.08, random_state: int = 42) -> None:
        self.contamination = contamination
        self.random_state = random_state
        self._model: Optional[IsolationForest] = None
        self._mean: float = 0.0
        self._std: float = 1.0
        self._amount_min: float = 0.0
        self._amount_range: float = 1.0
        self._merchant_counts: Counter = Counter()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _compute_stats(self, rows: list[dict]) -> None:
        """Pre-compute per-user statistics required for feature normalisation."""
        amounts = np.array([float(r["amount"]) for r in rows], dtype=np.float64)
        self._mean = float(np.mean(amounts))
        self._std = float(np.std(amounts)) or 1.0
        self._amount_min = float(amounts.min())
        self._amount_range = float(amounts.max() - amounts.min()) or 1.0
        self._merchant_counts = Counter(
            str(r.get("merchant") or "Unknown") for r in rows
        )

    def _build_feature_matrix(self, rows: list[dict]) -> np.ndarray:
        """Return an (N, 5) float32 feature matrix for the given rows."""
        matrix: list[list[float]] = []
        for row in rows:
            amount = float(row["amount"])
            dt = row.get("transaction_date")
            hour: int = getattr(dt, "hour", 12)
            weekday: int = getattr(dt, "weekday", lambda: 0)()
            merchant = str(row.get("merchant") or "Unknown")

            amount_norm = (amount - self._amount_min) / self._amount_range
            z_score = (amount - self._mean) / self._std
            rarity = 1.0 / max(self._merchant_counts[merchant], 1)

            matrix.append([amount_norm, hour, weekday, z_score, rarity])
        return np.array(matrix, dtype=np.float32)

    @staticmethod
    def _explain(
        row: dict,
        z_score: float,
        rarity: float,
        hour: int,
        amount: float,
        mean: float,
    ) -> tuple[list[str], str]:
        """
        Build (triggered_features, reason) by checking each feature against
        its heuristic threshold independently.
        """
        triggers: list[str] = []
        clauses: list[str] = []

        if abs(z_score) > _AMOUNT_ZSCORE_THRESHOLD:
            direction = "high" if z_score > 0 else "low"
            triggers.append("unusual_amount")
            clauses.append(
                f"the transaction amount (Rs {amount:,.2f}) is unusually {direction} "
                f"compared to your average spend (Rs {mean:,.2f})"
            )

        if rarity > _RARITY_THRESHOLD:
            triggers.append("rare_merchant")
            clauses.append(
                f"'{row.get('merchant', 'Unknown')}' is a merchant you rarely transact with"
            )

        if hour in _UNUSUAL_HOURS:
            triggers.append("unusual_timing")
            clauses.append(
                f"the transaction occurred at an unusual hour ({hour:02d}:xx)"
            )

        if not triggers:
            # Model flagged it on composite signal -- no single dominant feature
            triggers.append("composite_pattern")
            clauses.append(
                "a combination of amount, timing, and merchant pattern deviates "
                "from your historical norms"
            )

        reason = (
            "[STATISTICAL ANOMALY - NOT A FRAUD ALERT] "
            + "; ".join(clauses).capitalize()
            + ". Please verify with your bank if you are concerned."
        )
        return triggers, reason

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fit(self, rows: list[dict]) -> "TransactionAnomalyDetector":
        """
        Train the Isolation Forest on the user's historical transaction rows.

        Parameters
        ----------
        rows : list[dict]
            Each dict must contain: ``id``, ``amount``, ``transaction_date``,
            ``merchant``, ``category``.

        Returns
        -------
        self
        """
        if len(rows) < _MIN_SAMPLES:
            self._model = None
            return self
        self._compute_stats(rows)
        X = self._build_feature_matrix(rows)
        self._model = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state,
            n_estimators=200,
        )
        self._model.fit(X)
        return self

    def predict(self, rows: list[dict]) -> list[AnomalyResult]:
        """
        Score all rows and return only the flagged anomalies, sorted by
        anomaly score descending (most anomalous first).

        Parameters
        ----------
        rows : list[dict]
            Same schema as ``fit()``. Usually the same dataset (unsupervised).

        Returns
        -------
        list[AnomalyResult]
        """
        if self._model is None or not rows:
            return []

        X = self._build_feature_matrix(rows)
        labels: np.ndarray = self._model.predict(X)
        # decision_function: more-negative == more anomalous; we invert to a
        # positive anomaly_score so callers can sort descending.
        raw_scores: np.ndarray = -self._model.decision_function(X)

        results: list[AnomalyResult] = []
        for row, label, raw_score, feat in zip(rows, labels, raw_scores, X):
            if label != -1:
                continue

            amount = float(row["amount"])
            z_score = float(feat[3])
            rarity = float(feat[4])
            hour = int(feat[1])

            triggered_features, reason = self._explain(
                row, z_score, rarity, hour, amount, self._mean
            )

            results.append(
                AnomalyResult(
                    transaction_id=row.get("id"),
                    amount=amount,
                    merchant=str(row.get("merchant") or "Unknown"),
                    category=str(row.get("category") or "Other"),
                    transaction_date=row.get("transaction_date"),
                    anomaly_score=round(float(raw_score), 4),
                    triggered_features=triggered_features,
                    reason=reason,
                )
            )

        results.sort(key=lambda r: r.anomaly_score, reverse=True)
        return results


# ---------------------------------------------------------------------------
# Backward-compatible module-level function
# ---------------------------------------------------------------------------

def detect_anomalies(rows: list[dict], contamination: float = 0.08) -> list[dict]:
    """
    Thin wrapper around TransactionAnomalyDetector returning plain dicts.
    Existing call sites (e.g. routes/insights.py) require no changes.

    Note: trains and scores on the same dataset (fully unsupervised).
    This is for spending-pattern analysis ONLY, not fraud detection.
    """
    detector = TransactionAnomalyDetector(contamination=contamination)
    detector.fit(rows)
    return [r.to_dict() for r in detector.predict(rows)]
