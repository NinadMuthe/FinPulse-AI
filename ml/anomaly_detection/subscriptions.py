"""Heuristic recurring-payment detection from timestamped transactions."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
import statistics


def detect_subscriptions(rows: list[dict], min_count: int = 3) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        if str(row.get("transaction_type", "debit")).lower() != "debit":
            continue
        grouped[str(row.get("merchant", "Unknown")).lower()].append(row)

    found = []
    for merchant, items in grouped.items():
        if len(items) < min_count:
            continue
        def _as_dt(val):
            if isinstance(val, datetime):
                return val
            if isinstance(val, str):
                try:
                    return datetime.fromisoformat(val)
                except ValueError:
                    return datetime.strptime(val[:10], "%Y-%m-%d")
            return datetime.min

        items = sorted(items, key=lambda r: _as_dt(r["transaction_date"]))
        amounts = [float(r["amount"]) for r in items]
        median_amount = statistics.median(amounts)
        similar = [r for r in items if abs(float(r["amount"]) - median_amount) <= 0.15 * max(median_amount, 1)]
        if len(similar) < min_count:
            continue
        dates = [_as_dt(r["transaction_date"]) for r in similar]
        gaps = [(dates[i] - dates[i - 1]).days for i in range(1, len(dates))]
        if not gaps:
            continue
        typical_gap = int(statistics.median(gaps))
        if typical_gap < 7:
            continue
        gap_spread = statistics.pstdev(gaps) if len(gaps) > 1 else 0
        confidence = max(0.3, min(0.95, 0.9 - (gap_spread / max(typical_gap, 1)) * 0.4))
        interval = 30 if 25 <= typical_gap <= 35 else typical_gap
        found.append(
            {
                "merchant": similar[-1].get("merchant", merchant.title()),
                "typical_amount": round(median_amount, 2),
                "interval_days": interval,
                "occurrence_count": len(similar),
                "confidence": round(confidence, 3),
                "last_seen": dates[-1],
                "insight": (
                    f"You appear to have a recurring payment of approximately ₹{median_amount:.0f} "
                    f"about every {interval} days. Confidence is moderate, not a confirmed subscription."
                    if confidence < 0.75
                    else f"You appear to have a recurring payment of approximately ₹{median_amount:.0f} every {interval} days."
                ),
            }
        )
    return found
