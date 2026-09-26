from __future__ import annotations

import json

from vericell.pipeline import run_pipeline
from vericell.providers import (
    LiveProviderConfig,
    MockProvider,
    OpenAICompatibleProvider,
    ProviderError,
    ProviderResponse,
    parse_proposal,
)


def test_offline_pipeline_uses_mock_and_seals_once(tmp_path) -> None:
    config = {
        "data": {"samples": 80, "features": 6, "targets": 2, "groups": 8, "noise": 0.2, "seed": 7},
        "split": {"train": 0.6, "validation_working": 0.15, "validation_holdout": 0.15, "sealed_test": 0.1, "seed": 13},
        "workflow": {"alpha": 1.0, "seed": 101},
        "validation": {"gap_threshold": 0.2, "working_budget": 20},
    }
    provider = MockProvider(inject_violation_once=True)
    certificate = run_pipeline(config, tmp_path / "run", provider)
    assert provider.calls == 2
    assert certificate["certification"]["passed"] is True
    assert certificate["sealed_test_usage_count"] == 1
    assert certificate["repair_attempted"] is True
    assert certificate["repair_succeeded"] is True
    assert certificate["candidate_attempts"][0]["admission"]["admitted"] is False
    assert certificate["candidate_attempts"][1]["admission"]["admitted"] is True
    assert certificate["protocol_trace"]["runtime_events"] == []
    assert provider.messages[1][0]["role"] == "system"
    assert provider.messages[1][1]["content"].startswith("REPAIR:")
    assert json.loads((tmp_path / "run" / "certificate.json").read_text())["network_calls"] == 0


def test_rejected_candidate_never_reaches_final_evaluation(tmp_path) -> None:
    config = {
        "data": {"samples": 80, "features": 6, "targets": 2, "groups": 8, "noise": 0.2, "seed": 7},
        "split": {"train": 0.6, "validation_working": 0.15, "validation_holdout": 0.15, "sealed_test": 0.1, "seed": 13},
        "workflow": {"alpha": 1.0, "seed": 101},
        "validation": {"gap_threshold": 0.2, "working_budget": 20, "repair_budget": 0},
    }
    provider = MockProvider(inject_violation_once=True)
    try:
        run_pipeline(config, tmp_path / "rejected", provider)
    except RuntimeError as error:
        assert "candidate rejected" in str(error)
    else:
        raise AssertionError("an unrepaired violating candidate must be rejected")
    assert not (tmp_path / "rejected" / "certificate.json").exists()


def test_live_request_configuration_is_secret_free() -> None:
    response = ProviderResponse('{"model_family":"Ridge","preprocessing_steps":[],"modify_metrics":false,"modify_splits":false}', "offline", "offline", "OK")
    assert parse_proposal(response)["model_family"] == "Ridge"
    try:
        parse_proposal(ProviderResponse("not-json", "offline", "offline", "OK"))
    except ProviderError:
        pass
    else:
        raise AssertionError("malformed provider content must fail closed")


def test_live_payload_construction_does_not_call_network() -> None:
    provider = OpenAICompatibleProvider(LiveProviderConfig("https://example.invalid/v1", "test-model"))
    payload = provider.request_payload([{"role": "user", "content": "hello"}])
    assert payload["model"] == "test-model"
    assert payload["messages"][0]["content"] == "hello"
    assert "api_key" not in payload
