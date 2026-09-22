from __future__ import annotations

import json

from vericell.data import make_synthetic_dataset
from vericell.runner import run_demo
from vericell.splits import make_fixed_splits


def test_fixed_split_is_complete_and_disjoint() -> None:
    splits = make_fixed_splits(
        40,
        {"train": 0.6, "validation_working": 0.15, "validation_holdout": 0.15, "sealed_test": 0.1},
        13,
    )
    values = [index for indices in splits.values() for index in indices]
    assert len(values) == 40
    assert len(set(values)) == 40


def test_synthetic_fixture_is_deterministic() -> None:
    first = make_synthetic_dataset(samples=20, features=4, targets=2, groups=5, seed=7)
    second = make_synthetic_dataset(samples=20, features=4, targets=2, groups=5, seed=7)
    assert (first.features == second.features).all()
    assert (first.targets == second.targets).all()


def test_demo_writes_certified_artifacts(tmp_path) -> None:
    certificate = run_demo(output_dir=tmp_path / "run")
    assert certificate["certification"]["passed"] is True
    assert certificate["sealed_test_usage_count"] == 1
    saved = json.loads((tmp_path / "run" / "certificate.json").read_text(encoding="utf-8"))
    assert saved["network_calls"] == 0
    assert saved["provider_calls"] == 0
