"""Time-series forecasting baselines: 7-day Moving Average and Seasonal Naive models."""

from __future__ import annotations

import numpy as np


def moving_average_forecast(history: np.ndarray, horizon: int, window: int = 7) -> np.ndarray:
    """7-day Moving Average (MA) baseline forecast."""
    arr = np.asarray(history, dtype=np.float32)
    if len(arr) == 0:
        return np.zeros(horizon, dtype=np.float32)
    k = min(window, len(arr))
    mean_val = float(np.mean(arr[-k:]))
    return np.full(horizon, mean_val, dtype=np.float32)


def seasonal_naive_forecast(history: np.ndarray, horizon: int, season: int = 7) -> np.ndarray:
    """Seasonal Naive baseline repeating the last 7-day seasonal cycle across the forecast horizon."""
    arr = np.asarray(history, dtype=np.float32)
    if len(arr) < season:
        return moving_average_forecast(arr, horizon, window=len(arr) or 1)
    pattern = arr[-season:]
    repetitions = int(np.ceil(horizon / season))
    return np.tile(pattern, repetitions)[:horizon].astype(np.float32)


class MovingAverageBaseline:
    """Object-oriented wrapper for the Moving Average baseline."""

    def __init__(self, window: int = 7):
        self.window = window

    def predict(self, history: np.ndarray, horizon: int) -> np.ndarray:
        return moving_average_forecast(history, horizon, window=self.window)


class SeasonalNaiveBaseline:
    """Object-oriented wrapper for the Seasonal Naive baseline."""

    def __init__(self, season: int = 7):
        self.season = season

    def predict(self, history: np.ndarray, horizon: int) -> np.ndarray:
        return seasonal_naive_forecast(history, horizon, season=self.season)
