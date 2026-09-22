from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .metrics import compute_metrics


@dataclass
class WorkflowRun:
    workflow_id: str
    model_type: str
    pipeline: Pipeline
    metrics: dict[str, dict[str, float]]
    predictions: dict[str, np.ndarray]
    audit_log: dict[str, object]


def run_ridge_workflow(
    features: np.ndarray,
    targets: np.ndarray,
    splits: dict[str, list[int]],
    *,
    alpha: float = 1.0,
    seed: int = 101,
) -> WorkflowRun:
    """Fit exactly one local workflow with train-only preprocessing."""

    del seed  # retained in the contract for reproducible configuration records
    pipeline = Pipeline([("scaler", StandardScaler()), ("model", Ridge(alpha=float(alpha)))])
    train = np.asarray(splits["train"], dtype=int)
    pipeline.fit(features[train], targets[train])
    metrics: dict[str, dict[str, float]] = {}
    predictions: dict[str, np.ndarray] = {}
    for label in ("validation_working", "validation_holdout"):
        indices = np.asarray(splits[label], dtype=int)
        prediction = pipeline.predict(features[indices])
        predictions[label] = prediction
        metrics[label] = compute_metrics(targets[indices], prediction)
    audit_log: dict[str, object] = {
        "preprocessing_fit_split": "train",
        "model_fit_split": "train",
        "model_selection_splits": ["validation_working", "validation_holdout"],
        "input_columns": [f"feature_{i:03d}" for i in range(features.shape[1])],
        "target_columns": [f"target_{i:03d}" for i in range(targets.shape[1])],
        "metadata_columns": ["sample_id", "group_id"],
        "forbidden_input_columns": ["sample_id", "group_id"],
        "split_strategy": "fixed",
        "primary_metric": "pearson",
        "task_type": "regression",
    }
    return WorkflowRun("ridge_certified", "Ridge", pipeline, metrics, predictions, audit_log)
