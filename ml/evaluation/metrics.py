"""Evaluation metrics for time-series expenditure forecasting: MAE, RMSE, and MAPE."""

from __future__ import annotations

import numpy as np


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean Absolute Error (MAE) between true and predicted sequences."""
    y_t = np.asarray(y_true, dtype=np.float64)
    y_p = np.asarray(y_pred, dtype=np.float64)
    return float(np.mean(np.abs(y_t - y_p)))


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Root Mean Squared Error (RMSE) between true and predicted sequences."""
    y_t = np.asarray(y_true, dtype=np.float64)
    y_p = np.asarray(y_pred, dtype=np.float64)
    return float(np.sqrt(np.mean((y_t - y_p) ** 2)))


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float | None:
    """Mean Absolute Percentage Error (MAPE) ignoring near-zero actual values to prevent division by zero."""
    y_t = np.asarray(y_true, dtype=np.float64)
    y_p = np.asarray(y_pred, dtype=np.float64)
    mask = np.abs(y_t) > 1e-6
    if not np.any(mask):
        return None
    return float(np.mean(np.abs((y_t[mask] - y_p[mask]) / y_t[mask])) * 100.0)


def regression_report(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float | None]:
    """Calculate and return a dictionary containing MAE, RMSE, and MAPE."""
    report: dict[str, float | None] = {
        "mae": round(mae(y_true, y_pred), 4),
        "rmse": round(rmse(y_true, y_pred), 4),
    }
    mape_val = mape(y_true, y_pred)
    report["mape"] = None if mape_val is None else round(mape_val, 4)
    return report
