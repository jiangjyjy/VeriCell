"""Anonymous-release copy of the versioned workflow-rule evaluator.

This module validates explicit workflow evidence and evaluates the nine
manuscript protocol categories.  It is a local reference component, not a
claim that the complete provider-backed closed loop is included in this
anonymous package.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any


SCHEMA_VERSION = "v1.0"
CATEGORIES = [
    "Split leakage",
    "Preprocessing leakage",
    "Metric drift",
    "Target / perturbation leakage",
    "Batch shortcut",
    "Adaptive overfitting",
    "Statistical misuse",
    "Provenance loss",
    "Biological invalidity",
]
EVIDENCE_STATES = {"OBSERVED", "DECLARED_CONTRACT", "NOT_APPLICABLE", "UNKNOWN", "NOT_DECLARED"}


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(payload).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_workflow(workflow: dict[str, Any]) -> None:
    _require(isinstance(workflow, dict) and workflow.get("schema_version") == SCHEMA_VERSION, "SCHEMA_VERSION_MISMATCH")
    sections = ("data", "preprocessing", "metrics", "target_access", "batch", "validation", "statistics", "provenance", "biology", "field_evidence")
    for section in sections:
        _require(isinstance(workflow.get(section), dict), f"MISSING_SECTION:{section}")
    types = {
        "data.train_sources": list,
        "data.validation_sources": list,
        "data.holdout_sources": list,
        "data.protected_sources": list,
        "preprocessing.operations": list,
        "preprocessing.fit_scope": list,
        "metrics.optimization_metric": str,
        "metrics.evaluation_metrics": list,
        "metrics.metric_changes": list,
        "target_access.target_columns_used_as_features": list,
        "target_access.protected_data_access": bool,
        "target_access.perturbation_identity_used": bool,
        "batch.metadata_features": list,
        "validation.query_count": int,
        "validation.budget": int,
        "validation.feedback_used_for_updates": bool,
        "validation.adaptive_updates": bool,
        "statistics.experimental_unit": str,
        "statistics.multiplicity_policy": str,
        "statistics.posthoc_subgroup_selection": bool,
        "provenance.data_source_logged": bool,
        "provenance.preprocessing_logged": bool,
        "provenance.config_logged": bool,
        "provenance.seed_logged": bool,
        "provenance.artifact_hash": str,
        "biology.dose_feature_used": bool,
        "biology.perturbation_semantics_preserved": bool,
        "biology.biological_constraints_declared": bool,
    }
    for dotted, expected in types.items():
        section, field = dotted.split(".")
        _require(isinstance(workflow[section].get(field), expected), f"FIELD_INVALID:{dotted}")
    for dotted in types:
        _require(workflow["field_evidence"].get(dotted) in EVIDENCE_STATES, f"FIELD_EVIDENCE_INVALID:{dotted}")
    digest = workflow["provenance"]["artifact_hash"]
    _require(len(digest) == 64 and all(char in "0123456789abcdef" for char in digest.lower()), "ARTIFACT_HASH_INVALID")


def evaluate(workflow: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    validate_workflow(workflow)
    data, preprocessing, metrics, target, batch, validation, statistics, provenance, biology = (
        workflow[name]
        for name in ("data", "preprocessing", "metrics", "target_access", "batch", "validation", "statistics", "provenance", "biology")
    )
    evidence: dict[str, dict[str, Any]] = {}
    evidence[CATEGORIES[0]] = {"violation": bool(set(data["validation_sources"] + data["holdout_sources"] + data["protected_sources"]) & set(data["train_sources"])) or bool(data.get("fit_on_validation", False)) or bool(data.get("fit_on_holdout", False)), "evidence": "source overlap/non-training fit"}
    evidence[CATEGORIES[1]] = {"violation": any(item not in {"TRAIN", "NOT_APPLICABLE"} for item in preprocessing["fit_scope"]) or bool(preprocessing.get("fit_on_all_data", False)), "evidence": "preprocessing fit outside TRAIN"}
    evidence[CATEGORIES[2]] = {"violation": metrics["optimization_metric"].upper() not in {"PCC", "MSE", "R2"} or bool(metrics["metric_changes"]), "evidence": "non-frozen metric or metric change"}
    evidence[CATEGORIES[3]] = {"violation": bool(target["target_columns_used_as_features"]) or target["protected_data_access"] or target["perturbation_identity_used"], "evidence": "target/protected/perturbation identity used"}
    evidence[CATEGORIES[4]] = {"violation": bool(batch["metadata_features"]) or bool(batch.get("shortcut_detected", False)), "evidence": "batch metadata feature/shortcut"}
    evidence[CATEGORIES[5]] = {"violation": validation["query_count"] > validation["budget"], "evidence": "validation feedback exceeded declared budget"}
    evidence[CATEGORIES[6]] = {"violation": statistics["experimental_unit"] != "frozen_split_run" or statistics["multiplicity_policy"] in {"NONE", "UNSPECIFIED"} or statistics["posthoc_subgroup_selection"], "evidence": "invalid unit/multiplicity/post-hoc selection"}
    evidence[CATEGORIES[7]] = {"violation": not all(provenance[field] for field in ("data_source_logged", "preprocessing_logged", "config_logged", "seed_logged")) or len(provenance["artifact_hash"]) != 64, "evidence": "required provenance missing"}
    evidence[CATEGORIES[8]] = {"violation": (bool(task.get("requires_dose_feature", True)) and not biology["dose_feature_used"]) or not biology["perturbation_semantics_preserved"] or not biology["biological_constraints_declared"], "evidence": "dose/perturbation/biological contract not preserved"}
    return {"schema_version": SCHEMA_VERSION, "categories": evidence, "overall": sum(int(evidence[category]["violation"]) for category in CATEGORIES) / len(CATEGORIES)}


def evidence_map() -> dict[str, str]:
    """Return explicit provenance states used by the local reference fixture."""
    return {
        "data.train_sources": "OBSERVED", "data.validation_sources": "OBSERVED", "data.holdout_sources": "OBSERVED", "data.protected_sources": "OBSERVED",
        "preprocessing.operations": "OBSERVED", "preprocessing.fit_scope": "OBSERVED", "metrics.optimization_metric": "OBSERVED", "metrics.evaluation_metrics": "OBSERVED", "metrics.metric_changes": "OBSERVED",
        "target_access.target_columns_used_as_features": "OBSERVED", "target_access.protected_data_access": "OBSERVED", "target_access.perturbation_identity_used": "OBSERVED", "batch.metadata_features": "OBSERVED",
        "validation.query_count": "OBSERVED", "validation.budget": "DECLARED_CONTRACT", "validation.feedback_used_for_updates": "OBSERVED", "validation.adaptive_updates": "OBSERVED",
        "statistics.experimental_unit": "DECLARED_CONTRACT", "statistics.multiplicity_policy": "DECLARED_CONTRACT", "statistics.posthoc_subgroup_selection": "OBSERVED",
        "provenance.data_source_logged": "OBSERVED", "provenance.preprocessing_logged": "OBSERVED", "provenance.config_logged": "OBSERVED", "provenance.seed_logged": "OBSERVED", "provenance.artifact_hash": "OBSERVED",
        "biology.dose_feature_used": "DECLARED_CONTRACT", "biology.perturbation_semantics_preserved": "DECLARED_CONTRACT", "biology.biological_constraints_declared": "DECLARED_CONTRACT",
    }


def safe_workflow(seed: str = "safe", *, search_queries: int = 1) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "data": {"train_sources": ["TRAIN"], "validation_sources": ["VALIDATION"], "holdout_sources": ["HOLDOUT"], "protected_sources": ["PROTECTED"]},
        "preprocessing": {"operations": [], "fit_scope": ["NOT_APPLICABLE"]},
        "metrics": {"optimization_metric": "R2", "evaluation_metrics": ["R2"], "metric_changes": []},
        "target_access": {"target_columns_used_as_features": [], "protected_data_access": False, "perturbation_identity_used": False},
        "batch": {"metadata_features": [], "shortcut_detected": False},
        "validation": {"query_count": search_queries, "budget": 32, "feedback_used_for_updates": True, "adaptive_updates": True},
        "statistics": {"experimental_unit": "frozen_split_run", "multiplicity_policy": "predeclared", "posthoc_subgroup_selection": False},
        "provenance": {"data_source_logged": True, "preprocessing_logged": True, "config_logged": True, "seed_logged": True, "artifact_hash": hashlib.sha256(seed.encode()).hexdigest()},
        "biology": {"dose_feature_used": True, "perturbation_semantics_preserved": True, "biological_constraints_declared": True},
        "field_evidence": evidence_map(),
    }
