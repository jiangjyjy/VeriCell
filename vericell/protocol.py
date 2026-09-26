"""Executable protocol stages used by the public VeriCell pipeline.

The implementation follows the tested RQ2 mechanism path: static proposal
checks, runtime custody checks, audited validation, semantic artifact binding,
and fail-closed candidate admission.  It is intentionally independent of any
provider SDK.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


ALLOWED_MODELS = {"Ridge", "RealMLP", "RandomForestRegressor", "ExtraTreesRegressor"}


@dataclass
class RuntimeCustodyMonitor:
    protected_uri: str = "protected://decoy"
    events: list[dict[str, Any]] = field(default_factory=list)

    def inspect(self, proposal: dict[str, Any]) -> list[dict[str, Any]]:
        violations: list[dict[str, Any]] = []
        if any(role != "TRAIN" for role in proposal.get("training_row_roles", [])):
            violations.append(self._event("SPLIT_MEMBERSHIP_VIOLATION", "non-training row role used for fitting"))
        if proposal.get("result_affecting_validation_update"):
            violations.append(self._event("VALIDATION_MISUSE", "validation feedback changed the workflow"))
        resource = proposal.get("resource_request")
        if resource is not None:
            if resource != self.protected_uri:
                raise ValueError("protected access request did not use the declared decoy")
            violations.append(self._event("PROTECTED_DATA_ACCESS", "protected read blocked before file access"))
        return violations

    def _event(self, kind: str, message: str) -> dict[str, Any]:
        event = {"stage": "DYNAMIC_MONITORING", "violation_type": kind, "message": message}
        self.events.append(event)
        return event


@dataclass
class ValidationAuditor:
    working_budget: int = 20
    holdout_budget: int = 1
    sealed_budget: int = 1
    events: list[dict[str, Any]] = field(default_factory=list)

    def record(self, split: str, *, final_selection: bool = False, selected: bool = False) -> dict[str, Any]:
        count = sum(event["split"] == split for event in self.events)
        budget = {"validation_working": self.working_budget, "validation_holdout": self.holdout_budget, "sealed_test": self.sealed_budget}.get(split, 0)
        allowed = True
        reason = "within budget"
        if split == "sealed_test" and (not final_selection or not selected):
            allowed, reason = False, "sealed_test requires final selected workflow"
        elif count >= budget:
            allowed, reason = False, f"{split} budget exceeded"
        event = {"timestamp": datetime.now(UTC).isoformat(), "split": split, "allowed": allowed, "reason": reason}
        self.events.append(event)
        return event

    @property
    def violations(self) -> list[dict[str, Any]]:
        return [event for event in self.events if not event["allowed"]]


def static_certify(proposal: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if proposal.get("model_family") not in ALLOWED_MODELS:
        errors.append("UNSUPPORTED_MODEL")
    if any(step in {"fit_on_validation", "target_as_feature", "plate_identity"} for step in proposal.get("preprocessing_steps", [])):
        errors.append("FORBIDDEN_PREPROCESSING")
    if proposal.get("modify_metrics") or proposal.get("modify_splits"):
        errors.append("CONTRACT_MUTATION")
    return errors


def semantic_check(expected: str, observed: str) -> list[str]:
    return [] if expected == observed else ["PROVENANCE_OR_ARTIFACT_MISMATCH"]


def artifact_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def admit_candidate(static_errors: list[str], runtime_errors: list[dict[str, Any]], semantic_errors: list[str], audited_score: float) -> dict[str, Any]:
    errors = static_errors + [item["violation_type"] for item in runtime_errors] + semantic_errors
    return {"admitted": not errors, "audited_score": float(audited_score), "violations": errors}
