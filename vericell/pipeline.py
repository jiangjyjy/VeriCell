"""One configurable VeriCell execution path for offline and opt-in live runs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .certify import certify_workflow, validation_gap
from .data import make_synthetic_dataset
from .metrics import compute_metrics
from .providers import MockProvider, Provider, ProviderResponse, parse_proposal
from .protocol import RuntimeCustodyMonitor, ValidationAuditor, admit_candidate, artifact_hash, semantic_check, static_certify
from .splits import make_fixed_splits, save_splits
from .workflows import run_ridge_workflow


def run_pipeline(config: dict[str, Any], output_dir: str | Path, provider: Provider | None = None) -> dict[str, Any]:
    """Run one complete configured workflow and write a certificate.

    The default caller supplies :class:`MockProvider`; a live provider must be
    explicitly constructed by the caller.  No provider is contacted implicitly.
    """
    if provider is None:
        provider = MockProvider(inject_violation_once=True)
    data_cfg, split_cfg = config["data"], config["split"]
    bundle = make_synthetic_dataset(
        samples=int(data_cfg["samples"]), features=int(data_cfg["features"]), targets=int(data_cfg["targets"]),
        groups=int(data_cfg["groups"]), noise=float(data_cfg["noise"]), seed=int(data_cfg["seed"]),
    )
    fractions = {name: float(split_cfg[name]) for name in ("train", "validation_working", "validation_holdout", "sealed_test")}
    splits = make_fixed_splits(bundle.features.shape[0], fractions, int(split_cfg["seed"]))
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    save_splits(splits, out / "splits.json")

    repair_budget = int(config.get("validation", {}).get("repair_budget", 1))
    candidate_attempts: list[dict[str, Any]] = []
    messages = [{"role": "user", "content": "Propose a workflow using the frozen contract."}]
    final_response: ProviderResponse | None = None
    final_proposal: dict[str, Any] | None = None
    final_admission: dict[str, Any] | None = None
    for attempt_index in range(repair_budget + 1):
        response = provider.generate(messages)
        proposal = parse_proposal(response)
        static_errors = static_certify(proposal)
        runtime_errors = RuntimeCustodyMonitor().inspect(proposal)
        artifact_payload = {"proposal": proposal, "splits": splits}
        artifact_text = json.dumps(artifact_payload, sort_keys=True, separators=(",", ":"))
        artifact_path = out / f"candidate_artifact_attempt_{attempt_index + 1}.json"
        artifact_path.write_text(artifact_text, encoding="utf-8")
        expected_hash = artifact_hash(artifact_payload)
        observed_hash = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
        semantic_errors = semantic_check(expected_hash, observed_hash)
        auditor = ValidationAuditor(working_budget=int(config["validation"]["working_budget"]), holdout_budget=1, sealed_budget=1)
        query_count = max(1, int(proposal.get("validation_query_count", 0)))
        for _ in range(query_count):
            auditor.record("validation_working")
        auditor.record("validation_holdout")
        admission = admit_candidate(static_errors, runtime_errors + auditor.violations, semantic_errors, 1.0)
        candidate_attempts.append(
            {
                "attempt_index": attempt_index + 1,
                "provider_model": response.returned_model,
                "proposal": proposal,
                "static_errors": static_errors,
                "runtime_events": runtime_errors,
                "validation_events": auditor.events,
                "artifact_path": str(artifact_path.name),
                "artifact_expected_sha256": expected_hash,
                "artifact_observed_sha256": observed_hash,
                "admission": admission,
            }
        )
        final_response, final_proposal, final_admission = response, proposal, admission
        if admission["admitted"]:
            break
        if attempt_index >= repair_budget:
            raise RuntimeError(f"candidate rejected after {attempt_index + 1} attempts: {admission['violations']}")
        messages = [
            {"role": "system", "content": "Repair the workflow while preserving the frozen protocol contract."},
            {"role": "user", "content": "REPAIR:" + json.dumps({"violations": admission["violations"], "proposal": proposal}, sort_keys=True)},
        ]
    assert final_response is not None and final_proposal is not None and final_admission is not None

    workflow_cfg = config["workflow"]
    run = run_ridge_workflow(bundle.features, bundle.targets, splits, alpha=float(workflow_cfg["alpha"]), seed=int(workflow_cfg["seed"]))
    gap = validation_gap(run)
    certification = certify_workflow(run, gap, float(config["validation"]["gap_threshold"]))
    if not certification["passed"]:
        raise RuntimeError(f"workflow failed final certification: {certification['violations']}")
    sealed = splits["sealed_test"]
    final_auditor = ValidationAuditor(working_budget=int(config["validation"]["working_budget"]), holdout_budget=1, sealed_budget=1)
    final_event = final_auditor.record("sealed_test", final_selection=True, selected=True)
    if not final_event["allowed"]:
        raise RuntimeError("sealed-test access was not admitted")
    sealed_metrics = compute_metrics(bundle.targets[sealed], run.pipeline.predict(bundle.features[sealed]))
    certificate_core = {"workflow_id": run.workflow_id, "sealed_test_metrics": sealed_metrics}
    certificate = {
        "certificate_version": "1.3",
        "workflow_id": run.workflow_id,
        "provider_mode": "offline_mock" if isinstance(provider, MockProvider) else "live_opt_in",
        "provider_model": final_response.returned_model,
        "selection_metric": "pearson",
        "validation_gap": gap,
        "sealed_test_metrics": sealed_metrics,
        "sealed_test_usage_count": 1,
        "sealed_test_used_exactly_once": True,
        "certification": certification,
        "candidate_admission": final_admission,
        "candidate_attempts": candidate_attempts,
        "repair_attempted": len(candidate_attempts) > 1,
        "repair_succeeded": len(candidate_attempts) > 1 and final_admission["admitted"],
        "protocol_trace": {"static_errors": candidate_attempts[-1]["static_errors"], "runtime_events": candidate_attempts[-1]["runtime_events"], "validation_events": candidate_attempts[-1]["validation_events"] + [final_event]},
        "data_contract": {"sample_count": int(bundle.features.shape[0]), "feature_count": int(bundle.features.shape[1]), "target_count": int(bundle.targets.shape[1]), "target_names": list(bundle.target_names)},
        "network_calls": 0 if isinstance(provider, MockProvider) else 1,
        "provider_calls": len(candidate_attempts),
        "training_runs": 1,
        "artifact_hash": hashlib.sha256(json.dumps(certificate_core, sort_keys=True).encode()).hexdigest(),
    }
    (out / "certificate.json").write_text(json.dumps(certificate, indent=2) + "\n", encoding="utf-8")
    return certificate
