"""Simple seasonal-naive / moving-average baseline used before LSTM."""

from __future__ import annotations

import numpy as np


def moving_average_forecast(history: np.ndarray, horizon: int, window: int = 7) -> np.ndarray:
    if len(history) == 0:
        return np.zeros(horizon, dtype=np.float32)
    k = min(window, len(history))
    mean = float(np.mean(history[-k:]))
    return np.full(horizon, mean, dtype=np.float32)


def seasonal_naive_forecast(history: np.ndarray, horizon: int, season: int = 7) -> np.ndarray:
    if len(history) < season:
        return moving_average_forecast(history, horizon, window=len(history) or 1)
    pattern = history[-season:]
    reps = int(np.ceil(horizon / season))
    return np.tile(pattern, reps)[:horizon].astype(np.float32)
