from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from .certify import certify_workflow, validation_gap
from .data import make_synthetic_dataset
from .metrics import compute_metrics
from .splits import make_fixed_splits, save_splits
from .workflows import run_ridge_workflow


def run_demo(config_path: str | Path | None = None, output_dir: str | Path = "outputs/demo") -> dict[str, Any]:
    """Run the complete offline demonstration and write a compact certificate."""

    config = _load_config(config_path)
    data_cfg = config["data"]
    split_cfg = config["split"]
    workflow_cfg = config["workflow"]
    bundle = make_synthetic_dataset(
        samples=int(data_cfg["samples"]),
        features=int(data_cfg["features"]),
        targets=int(data_cfg["targets"]),
        groups=int(data_cfg["groups"]),
        noise=float(data_cfg["noise"]),
        seed=int(data_cfg["seed"]),
    )
    fractions = {name: float(split_cfg[name]) for name in ("train", "validation_working", "validation_holdout", "sealed_test")}
    splits = make_fixed_splits(bundle.features.shape[0], fractions, int(split_cfg["seed"]))
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    save_splits(splits, out / "splits.json")

    run = run_ridge_workflow(
        bundle.features,
        bundle.targets,
        splits,
        alpha=float(workflow_cfg["alpha"]),
        seed=int(workflow_cfg["seed"]),
    )
    gap = validation_gap(run)
    certification = certify_workflow(run, gap, float(config["validation"]["gap_threshold"]))
    if not certification["passed"]:
        raise RuntimeError(f"workflow did not pass certification: {certification['violations']}")

    sealed = splits["sealed_test"]
    sealed_prediction = run.pipeline.predict(bundle.features[sealed])
    sealed_metrics = compute_metrics(bundle.targets[sealed], sealed_prediction)
    certificate = {
        "certificate_version": "1.0",
        "workflow_id": run.workflow_id,
        "model_type": run.model_type,
        "selection_metric": "pearson",
        "validation_gap": gap,
        "sealed_test_metrics": sealed_metrics,
        "sealed_test_usage_count": 1,
        "sealed_test_used_exactly_once": True,
        "certification": certification,
        "data_contract": {
            "sample_count": int(bundle.features.shape[0]),
            "feature_count": int(bundle.features.shape[1]),
            "target_count": int(bundle.targets.shape[1]),
            "target_names": list(bundle.target_names),
        },
        "network_calls": 0,
        "provider_calls": 0,
        "training_runs": 1,
    }
    (out / "certificate.json").write_text(json.dumps(certificate, indent=2) + "\n", encoding="utf-8")
    (out / "run_summary.json").write_text(
        json.dumps({"validation": run.metrics, "sealed_test": sealed_metrics}, indent=2) + "\n",
        encoding="utf-8",
    )
    return certificate


def _load_config(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "data": {"samples": 240, "features": 16, "targets": 3, "groups": 24, "noise": 0.25, "seed": 7},
            "split": {"train": 0.60, "validation_working": 0.15, "validation_holdout": 0.15, "sealed_test": 0.10, "seed": 13},
            "workflow": {"model": "ridge", "alpha": 1.0, "seed": 101},
            "validation": {"gap_threshold": 0.20},
        }
    with Path(path).open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)
