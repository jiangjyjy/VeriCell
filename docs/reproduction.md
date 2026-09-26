# Reproduction guide

## Quick offline check

With Python 3.10+ and the declared dependencies installed:

```bash
python -m pytest -q
python scripts/run_pipeline.py --mode offline --config configs/default.yaml --output outputs/pipeline
python run_demo.py --config configs/default.yaml --output outputs/demo
python scripts/replay_results.py --all
```

These commands are local-only.  The pipeline command exercises proposal
parsing, static certification, runtime custody monitoring, audited validation,
candidate admission, and one final evaluation using the deterministic mock
provider.  The replay command reads packaged tables and reports their
provenance class; it does not infer predictions from aggregate metrics.

## Scope boundaries

The offline synthetic workflow is the end-to-end runnable path in this release.
The manuscript tables are included for reviewer inspection, while a full
benchmark replay is not claimed because raw datasets, complete frozen splits,
target-order manifests, per-sample predictions, and checkpoints are not
distributed.  Provider-backed experiments are opt-in and are intentionally not
invoked by any default command.

## Dataset-dependent reruns

A benchmark rerun requires the exact public dataset release, split and target
manifests, preprocessing state, baseline implementations, and sufficient
compute.  Consult `data/README.md` and verify all external sources and licenses
before adding data locally.
