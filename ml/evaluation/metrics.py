from __future__ import annotations

import numpy as np


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs(y_true - y_pred)))


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float | None:
    mask = np.abs(y_true) > 1e-6
    if not np.any(mask):
        return None
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def regression_report(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    report = {"mae": round(mae(y_true, y_pred), 4), "rmse": round(rmse(y_true, y_pred), 4)}
    mape_value = mape(y_true, y_pred)
    report["mape"] = None if mape_value is None else round(mape_value, 4)
    return report
