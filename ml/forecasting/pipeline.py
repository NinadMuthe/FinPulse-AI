"""End-to-end spend forecast: baseline first, LSTM when data and PyTorch allow."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ml.evaluation.metrics import regression_report
from ml.forecasting.baseline import moving_average_forecast, seasonal_naive_forecast
from ml.preprocessing.timeseries import (
    chronological_split,
    minmax_fit,
    minmax_inverse,
    minmax_transform,
    sliding_windows,
    transactions_to_daily_spend,
)

MODEL_DIR = Path("ml/models")
WINDOW = 14


def forecast_spend(rows: list[dict], horizon: int = 30) -> dict:
    daily = transactions_to_daily_spend(rows)
    series = daily["spend"].to_numpy(dtype=np.float32) if len(daily) else np.array([], dtype=np.float32)
    baseline = moving_average_forecast(series, horizon)
    seasonal = seasonal_naive_forecast(series, horizon)
    metrics = {"baseline": {}, "lstm": None, "note": "Chronological split only; no random shuffle."}

    if len(series) >= WINDOW + horizon:
        train, val, test = chronological_split(series)
        x_tr, y_tr = sliding_windows(train, WINDOW, min(horizon, 15))
        x_va, y_va = sliding_windows(np.concatenate([train[-WINDOW:], val]) if len(val) else train, WINDOW, min(horizon, 15))
        if len(x_tr):
            y_hat = np.array([moving_average_forecast(x, y_tr.shape[1]) for x in x_tr])
            metrics["baseline"] = regression_report(y_tr, y_hat)
        lstm_pred = _try_lstm(train, val, series, horizon)
        if lstm_pred is not None:
            predicted, lstm_metrics = lstm_pred
            metrics["lstm"] = lstm_metrics
            model_name = "lstm"
            used = predicted
        else:
            model_name = "seasonal_naive"
            used = seasonal
            if len(test) >= 7:
                metrics["baseline"] = regression_report(test[: min(len(test), horizon)], seasonal[: min(len(test), horizon)])
    else:
        model_name = "moving_average"
        used = baseline
        metrics["note"] += " Not enough daily history for LSTM windows."

    predicted_spend = float(np.sum(used[:horizon]))
    return {
        "daily_forecast": [round(float(x), 2) for x in used[:horizon]],
        "baseline_daily_forecast": [round(float(x), 2) for x in baseline[:horizon]],
        "seasonal_daily_forecast": [round(float(x), 2) for x in seasonal[:horizon]],
        "predicted_spend": round(predicted_spend, 2),
        "baseline_predicted_spend": round(float(np.sum(baseline[:horizon])), 2),
        "model_name": model_name,
        "metrics": metrics,
        "history_days": int(len(series)),
    }


def _try_lstm(train, val, series, horizon):
    try:
        from ml.forecasting.lstm_model import predict_lstm, train_lstm
    except Exception:
        return None
    try:
        low, high = minmax_fit(train)
        train_n = minmax_transform(train, low, high)
        val_n = minmax_transform(val, low, high) if len(val) else np.array([])
        h = min(horizon, 15)
        x_tr, y_tr = sliding_windows(train_n, WINDOW, h)
        concat_val = np.concatenate([train_n[-WINDOW:], val_n]) if len(val_n) else train_n
        x_va, y_va = sliding_windows(concat_val, WINDOW, h)
        if len(x_tr) < 4:
            return None
        model = train_lstm(x_tr, y_tr, x_va, y_va, epochs=25)
        pred_n = predict_lstm(model, train_n[-WINDOW:] if len(val_n) == 0 else concat_val[-WINDOW:])
        pred = minmax_inverse(pred_n, low, high)
        if len(x_va):
            va_hat = np.array([minmax_inverse(predict_lstm(model, row), low, high) for row in x_va])
            va_true = minmax_inverse(y_va, low, high)
            metrics = regression_report(va_true, va_hat)
        else:
            metrics = {}
        if horizon > len(pred):
            extra = moving_average_forecast(series, horizon - len(pred))
            pred = np.concatenate([pred, extra])
        return pred[:horizon], metrics
    except Exception:
        return None


def persist_metrics(payload: dict, path: Path | None = None) -> None:
    target = path or MODEL_DIR / "last_forecast_metrics.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
