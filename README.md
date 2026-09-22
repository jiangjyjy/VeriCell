# Vericell

## Protocol-Certified Workflow Search for Cellular Perturbation-Response Prediction

Vericell is a protocol-aware framework for selecting and evaluating predictive
workflows for cellular perturbation-response data. The implementation makes
the experimental protocol explicit and records the evidence needed to audit a
final model evaluation.

The reference pipeline provides deterministic data construction, fixed
train/working-validation/holdout/sealed-test partitions, train-only
preprocessing, validation-based workflow certification, and a single final
evaluation on the sealed test partition. Each run emits machine-readable
metrics and a certificate describing the checks that were applied.

## Protocol guarantees

- Partition membership is generated deterministically from a recorded seed.
- Preprocessing is fitted on the training partition only.
- The sealed test partition is excluded from workflow selection.
- Validation behavior and target/metadata isolation are checked explicitly.
- The selected workflow is evaluated on the sealed test partition once.
- Configuration, metrics, and certification decisions are written as JSON.

## Repository structure

```text
vericell/
  data.py       deterministic data contract and fixture construction
  splits.py     fixed partition construction and validation
  workflows.py  train-only preprocessing and workflow execution
  certify.py    protocol checks and validation-gap certification
  metrics.py    regression metrics
  runner.py     end-to-end execution and certificate generation
run_demo.py     command-line entry point
configs/        reproducible default configuration
tests/          local regression and smoke tests
```

## Installation

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

## Running the reference pipeline

```bash
python run_demo.py --config configs/default.yaml --output outputs/demo
```

The command writes `splits.json`, `run_summary.json`, and `certificate.json`
under the requested output directory. Output directories are excluded from
version control by default.

## Verification

```bash
python -m pytest -q
```

The default configuration uses a deterministic synthetic regression fixture so
that the protocol and certification logic can be exercised without external
data. Dataset-specific adapters can be integrated through the same data,
split, workflow, and certificate interfaces while preserving the protocol
checks above.
