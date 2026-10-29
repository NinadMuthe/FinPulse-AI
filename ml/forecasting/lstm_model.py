"""Compact PyTorch LSTM for daily expenditure sequences.

Architecture:
    SpendLSTM: Recurrent neural network with an LSTM layer and linear prediction head.
Training:
    Sliding window (W=14) with strict chronological data splitting (70% train, 15% val, 15% test)
    without random shuffling to prevent lookahead bias.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from ml.evaluation.metrics import regression_report

try:
    import torch
    from torch import nn
except ImportError:  # pragma: no cover - optional dependency
    torch = None
    nn = None


class SpendLSTM(nn.Module if nn is not None else object):  # type: ignore[misc]
    """Recurrent neural network with an LSTM layer and a linear prediction head."""

    def __init__(self, hidden_size: int = 32, num_layers: int = 1, horizon: int = 15):
        if torch is None:
            raise ImportError("PyTorch is required for LSTM forecasting")
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.horizon = horizon
        self.lstm = nn.LSTM(
            input_size=1,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
        )
        self.head = nn.Linear(hidden_size, horizon)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Pass input sequence through LSTM and project final hidden state to prediction horizon."""
        output, _ = self.lstm(x)
        last_hidden = output[:, -1, :]
        return self.head(last_hidden)


def train_spend_lstm_chronological(
    series: np.ndarray,
    window_size: int = 14,
    horizon: int = 15,
    epochs: int = 30,
    lr: float = 1e-3,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
) -> tuple[SpendLSTM | None, dict[str, Any]]:
    """Train SpendLSTM using sliding window (W=14) and strict chronological split (70% / 15% / 15%).

    No random shuffling is applied to prevent time-series lookahead bias.
    """
    if torch is None:
        return None, {"error": "PyTorch not installed"}

    series = np.asarray(series, dtype=np.float32)
    n = len(series)
    if n < window_size + horizon:
        return None, {"error": "Insufficient historical points for W=14 + horizon window"}

    # Strict chronological partition
    train_end = max(1, int(n * train_ratio))
    val_end = max(train_end + 1, int(n * (train_ratio + val_ratio)))

    train_raw = series[:train_end]
    val_raw = series[train_end:val_end]
    test_raw = series[val_end:]

    # Scale strictly on train split to prevent data leakage
    low = float(np.min(train_raw))
    high = float(np.max(train_raw))
    if high - low < 1e-6:
        high = low + 1.0

    def scale(arr: np.ndarray) -> np.ndarray:
        return (arr - low) / (high - low)

    def inv_scale(arr: np.ndarray) -> np.ndarray:
        return arr * (high - low) + low

    def make_windows(arr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        xs, ys = [], []
        for i in range(len(arr) - window_size - horizon + 1):
            xs.append(arr[i : i + window_size])
            ys.append(arr[i + window_size : i + window_size + horizon])
        if not xs:
            return np.empty((0, window_size), dtype=np.float32), np.empty((0, horizon), dtype=np.float32)
        return np.array(xs, dtype=np.float32), np.array(ys, dtype=np.float32)

    train_scaled = scale(train_raw)
    x_tr, y_tr = make_windows(train_scaled)

    # For validation and test windows, stitch preceding context to capture boundary sequences
    val_seq = np.concatenate([train_scaled[-window_size:], scale(val_raw)]) if len(val_raw) else train_scaled
    x_va, y_va = make_windows(val_seq)

    test_seq = np.concatenate([val_seq[-window_size:], scale(test_raw)]) if len(test_raw) else val_seq
    x_te, y_te = make_windows(test_seq)

    if len(x_tr) < 2:
        return None, {"error": "Too few training windows"}

    model = SpendLSTM(hidden_size=32, num_layers=1, horizon=horizon)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()

    x_tr_tensor = torch.tensor(x_tr[..., None], dtype=torch.float32)
    y_tr_tensor = torch.tensor(y_tr, dtype=torch.float32)
    x_va_tensor = torch.tensor(x_va[..., None], dtype=torch.float32) if len(x_va) else None
    y_va_tensor = torch.tensor(y_va, dtype=torch.float32) if len(y_va) else None

    model.train()
    for _ in range(epochs):
        optimizer.zero_grad()
        pred = model(x_tr_tensor)
        loss = loss_fn(pred, y_tr_tensor)
        loss.backward()
        optimizer.step()

        if x_va_tensor is not None and len(x_va_tensor):
            model.eval()
            with torch.no_grad():
                _ = loss_fn(model(x_va_tensor), y_va_tensor)
            model.train()

    # Evaluation on validation and test sets (inverse transformed)
    metrics: dict[str, Any] = {
        "train_samples": len(x_tr),
        "val_samples": len(x_va),
        "test_samples": len(x_te),
        "split": "70% train / 15% validation / 15% test (chronological, no shuffle)",
        "window_size": window_size,
        "horizon": horizon,
    }

    model.eval()
    with torch.no_grad():
        if len(x_va):
            pred_va_norm = model(torch.tensor(x_va[..., None], dtype=torch.float32)).numpy()
            pred_va = inv_scale(pred_va_norm)
            true_va = inv_scale(y_va)
            metrics["val_metrics"] = regression_report(true_va, pred_va)
        if len(x_te):
            pred_te_norm = model(torch.tensor(x_te[..., None], dtype=torch.float32)).numpy()
            pred_te = inv_scale(pred_te_norm)
            true_te = inv_scale(y_te)
            metrics["test_metrics"] = regression_report(true_te, pred_te)

    return model, metrics


def train_lstm(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray,
    y_val: np.ndarray,
    epochs: int = 30,
    lr: float = 1e-3,
) -> SpendLSTM:
    """Train SpendLSTM on pre-windowed numpy arrays."""
    if torch is None:
        raise ImportError("PyTorch is required for LSTM forecasting")
    model = SpendLSTM(horizon=y_train.shape[1])
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()
    x_t = torch.tensor(x_train[..., None], dtype=torch.float32)
    y_t = torch.tensor(y_train, dtype=torch.float32)
    x_v = torch.tensor(x_val[..., None], dtype=torch.float32) if len(x_val) else None
    y_v = torch.tensor(y_val, dtype=torch.float32) if len(y_val) else None

    model.train()
    for _ in range(epochs):
        optimizer.zero_grad()
        pred = model(x_t)
        loss = loss_fn(pred, y_t)
        loss.backward()
        optimizer.step()
        if x_v is not None and len(x_v):
            model.eval()
            with torch.no_grad():
                _ = loss_fn(model(x_v), y_v)
            model.train()
    return model


def predict_lstm(model: SpendLSTM, window: np.ndarray) -> np.ndarray:
    """Predict horizon values given a single input window."""
    if torch is None:
        raise ImportError("PyTorch is required for LSTM forecasting")
    model.eval()
    with torch.no_grad():
        x = torch.tensor(window.reshape(1, -1, 1), dtype=torch.float32)
        return model(x).numpy()[0]


def save_model(model: SpendLSTM, path: Path) -> None:
    if torch is None:
        raise ImportError("PyTorch is required for LSTM forecasting")
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), path)


def load_model(path: Path, horizon: int) -> SpendLSTM:
    model = SpendLSTM(horizon=horizon)
    state = __import__("torch").load(path, map_location="cpu")
    model.load_state_dict(state)
    model.eval()
    return model
