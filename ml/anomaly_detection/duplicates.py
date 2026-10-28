"""Deterministic near-duplicate matching. Not Isolation Forest."""

from __future__ import annotations

from datetime import datetime


def find_duplicates(rows: list[dict], amount_tol: float = 0.01, hours: float = 2.0) -> list[dict]:
    duplicates = []
    def _as_dt(val):
        if isinstance(val, datetime):
            return val
        if isinstance(val, str):
            try:
                return datetime.fromisoformat(val)
            except ValueError:
                return datetime.strptime(val[:10], "%Y-%m-%d")
        return datetime.min

    sorted_rows = sorted(rows, key=lambda r: _as_dt(r["transaction_date"]))
    for i, left in enumerate(sorted_rows):
        for right in sorted_rows[i + 1 :]:
            left_dt = _as_dt(left["transaction_date"])
            right_dt = _as_dt(right["transaction_date"])
            delta_hours = abs((right_dt - left_dt).total_seconds()) / 3600
            if delta_hours > hours:
                break
            same_merchant = left.get("merchant", "").lower() == right.get("merchant", "").lower()
            amount_close = abs(float(left["amount"]) - float(right["amount"])) <= amount_tol * max(float(left["amount"]), 1.0)
            same_source = left.get("source") == right.get("source")
            if same_merchant and amount_close:
                duplicates.append(
                    {
                        "left_id": left.get("id"),
                        "right_id": right.get("id"),
                        "merchant": left.get("merchant"),
                        "amount": left.get("amount"),
                        "hours_apart": round(delta_hours, 3),
                        "reason": "Likely duplicate: similar merchant, amount, and timestamp"
                        + (" and same source" if same_source else ""),
                    }
                )
    return duplicates
