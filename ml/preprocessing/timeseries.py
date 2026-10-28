"""Daily aggregation and chronological windowing. Never shuffle time-series rows."""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd


def transactions_to_daily_spend(rows: list[dict], end_date: date | None = None) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=["date", "spend"])
    frame = pd.DataFrame(rows)
    frame["transaction_date"] = pd.to_datetime(frame["transaction_date"])
    debits = frame[frame["transaction_type"].str.lower() == "debit"].copy()
    if debits.empty:
        return pd.DataFrame(columns=["date", "spend"])
    daily = (
        debits.groupby(debits["transaction_date"].dt.date)["amount"]
        .sum()
        .reset_index()
        .rename(columns={"transaction_date": "date", "amount": "spend"})
    )
    start = daily["date"].min()
    finish = end_date or daily["date"].max()
    calendar = pd.DataFrame({"date": [start + timedelta(days=i) for i in range((finish - start).days + 1)]})
    merged = calendar.merge(daily, on="date", how="left").fillna({"spend": 0.0})
    return merged.sort_values("date").reset_index(drop=True)


def chronological_split(series: np.ndarray, train_ratio: float = 0.7, val_ratio: float = 0.15):
    n = len(series)
    train_end = max(1, int(n * train_ratio))
    val_end = max(train_end + 1, int(n * (train_ratio + val_ratio)))
    return series[:train_end], series[train_end:val_end], series[val_end:]


def sliding_windows(series: np.ndarray, window: int, horizon: int) -> tuple[np.ndarray, np.ndarray]:
    xs, ys = [], []
    for i in range(len(series) - window - horizon + 1):
        xs.append(series[i : i + window])
        ys.append(series[i + window : i + window + horizon])
    if not xs:
        return np.empty((0, window)), np.empty((0, horizon))
    return np.array(xs, dtype=np.float32), np.array(ys, dtype=np.float32)


def minmax_fit(series: np.ndarray) -> tuple[float, float]:
    low = float(np.min(series))
    high = float(np.max(series))
    if high - low < 1e-6:
        high = low + 1.0
    return low, high


def minmax_transform(series: np.ndarray, low: float, high: float) -> np.ndarray:
    return (series - low) / (high - low)


def minmax_inverse(series: np.ndarray, low: float, high: float) -> np.ndarray:
    return series * (high - low) + low
