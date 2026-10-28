"""Compact LSTM for daily spend sequences. Training is separate from inference."""

from __future__ import annotations

from pathlib import Path

import numpy as np

try:
    import torch
    from torch import nn
except ImportError:  # pragma: no cover - optional dependency
    torch = None
    nn = None


class SpendLSTM(nn.Module if nn is not None else object):  # type: ignore[misc]
    def __init__(self, hidden_size: int = 32, num_layers: int = 1, horizon: int = 15):
        if torch is None:
            raise ImportError("PyTorch is required for LSTM forecasting")
        super().__init__()
        self.lstm = nn.LSTM(input_size=1, hidden_size=hidden_size, num_layers=num_layers, batch_first=True)
        self.head = nn.Linear(hidden_size, horizon)

    def forward(self, x):
        output, _ = self.lstm(x)
        last = output[:, -1, :]
        return self.head(last)


def train_lstm(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray,
    y_val: np.ndarray,
    epochs: int = 30,
    lr: float = 1e-3,
) -> SpendLSTM:
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
