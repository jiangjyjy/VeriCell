from __future__ import annotations

import json
from pathlib import Path

import numpy as np

LABELS = ("train", "validation_working", "validation_holdout", "sealed_test")


def make_fixed_splits(samples: int, fractions: dict[str, float], seed: int) -> dict[str, list[int]]:
    """Create a deterministic, disjoint index split."""

    if set(fractions) != set(LABELS):
        raise ValueError(f"fractions must contain exactly {LABELS}")
    if not np.isclose(sum(float(fractions[name]) for name in LABELS), 1.0):
        raise ValueError("split fractions must sum to one")
    if samples < 4:
        raise ValueError("at least four samples are required")
    shuffled = np.random.default_rng(seed).permutation(samples)
    sizes = [int(round(samples * float(fractions[name]))) for name in LABELS[:-1]]
    sizes.append(samples - sum(sizes))
    result: dict[str, list[int]] = {}
    start = 0
    for name, size in zip(LABELS, sizes, strict=True):
        result[name] = sorted(int(i) for i in shuffled[start : start + size])
        start += size
    _validate(result, samples)
    return result


def save_splits(splits: dict[str, list[int]], path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(splits, indent=2) + "\n", encoding="utf-8")


def _validate(splits: dict[str, list[int]], samples: int) -> None:
    values = [index for name in LABELS for index in splits[name]]
    if len(values) != samples or len(set(values)) != samples or set(values) != set(range(samples)):
        raise ValueError("split indices are not a complete disjoint partition")
