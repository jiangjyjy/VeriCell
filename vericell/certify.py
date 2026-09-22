from __future__ import annotations

from typing import Any

from .workflows import WorkflowRun


def validation_gap(run: WorkflowRun) -> dict[str, float]:
    working = run.metrics["validation_working"]["pearson"]
    holdout = run.metrics["validation_holdout"]["pearson"]
    return {
        "primary_metric": "pearson",
        "validation_working_score": working,
        "audited_validation_score": holdout,
        "validation_gap": float(working - holdout),
    }


def certify_workflow(run: WorkflowRun, gap: dict[str, float], threshold: float) -> dict[str, Any]:
    checks = {
        "preprocessing_fit_train_only": run.audit_log.get("preprocessing_fit_split") == "train",
        "sealed_test_not_used_for_selection": "sealed_test" not in run.audit_log.get("model_selection_splits", []),
        "target_columns_excluded": not set(run.audit_log.get("input_columns", [])).intersection(
            run.audit_log.get("target_columns", [])
        ),
        "metadata_columns_excluded": not set(run.audit_log.get("input_columns", [])).intersection(
            set(run.audit_log.get("metadata_columns", [])) | set(run.audit_log.get("forbidden_input_columns", []))
        ),
        "validation_gap_within_threshold": gap["validation_gap"] <= float(threshold),
    }
    violations = [name for name, passed in checks.items() if not passed]
    return {"passed": not violations, "passed_checks": checks, "violations": violations}
