from __future__ import annotations

import numpy as np


def pearson(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    true = np.asarray(y_true, dtype=float).ravel()
    pred = np.asarray(y_pred, dtype=float).ravel()
    if true.size == 0 or np.std(true) == 0.0 or np.std(pred) == 0.0:
        return 0.0
    return float(np.corrcoef(true, pred)[0, 1])


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    true = np.asarray(y_true, dtype=float)
    pred = np.asarray(y_pred, dtype=float)
    if true.shape != pred.shape:
        raise ValueError(f"shape mismatch: {true.shape} != {pred.shape}")
    residual = true - pred
    mse = float(np.mean(residual**2))
    variance = float(np.sum((true - np.mean(true)) ** 2))
    return {
        "mse": mse,
        "rmse": float(np.sqrt(mse)),
        "mae": float(np.mean(np.abs(residual))),
        "pearson": pearson(true, pred),
        "r2": float(1.0 - np.sum(residual**2) / variance) if variance else 0.0,
    }
