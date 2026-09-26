from __future__ import annotations

from vericell.protocol_reference import CATEGORIES, evaluate, safe_workflow


def test_clean_reference_workflow_has_no_violations() -> None:
    result = evaluate(safe_workflow("test"), {"requires_dose_feature": True})
    assert result["overall"] == 0
    assert all(not result["categories"][category]["violation"] for category in CATEGORIES)


def test_reference_evaluator_detects_an_explicit_overlap() -> None:
    workflow = safe_workflow("test")
    workflow["data"]["validation_sources"] = ["TRAIN"]
    workflow["data"]["fit_on_validation"] = True
    result = evaluate(workflow, {"requires_dose_feature": True})
    assert result["categories"]["Split leakage"]["violation"] is True
