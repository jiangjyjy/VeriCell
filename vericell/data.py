from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class DatasetBundle:
    """In-memory data contract used by the local workflow."""

    features: np.ndarray
    targets: np.ndarray
    sample_ids: tuple[str, ...]
    group_ids: tuple[str, ...]
    feature_names: tuple[str, ...]
    target_names: tuple[str, ...]


def make_synthetic_dataset(
    *,
    samples: int = 240,
    features: int = 16,
    targets: int = 3,
    groups: int = 24,
    noise: float = 0.25,
    seed: int = 7,
) -> DatasetBundle:
    """Create a deterministic grouped regression fixture without I/O."""

    if min(samples, features, targets, groups) <= 0:
        raise ValueError("dataset dimensions must be positive")
    if groups > samples:
        raise ValueError("groups cannot exceed samples")
    rng = np.random.default_rng(seed)
    group_index = rng.integers(0, groups, size=samples)
    base = rng.normal(size=(samples, features))
    group_effect = rng.normal(scale=0.7, size=(groups, features))
    x = base + group_effect[group_index]
    weights = rng.normal(scale=0.8, size=(features, targets))
    nonlinear = np.sin(x[:, : min(4, features)]).sum(axis=1, keepdims=True)
    y = x @ weights + 0.35 * nonlinear + rng.normal(scale=noise, size=(samples, targets))
    return DatasetBundle(
        features=x.astype(np.float64),
        targets=y.astype(np.float64),
        sample_ids=tuple(f"sample_{i:05d}" for i in range(samples)),
        group_ids=tuple(f"group_{i:03d}" for i in group_index),
        feature_names=tuple(f"feature_{i:03d}" for i in range(features)),
        target_names=tuple(f"target_{i:03d}" for i in range(targets)),
    )
