# Vericell ICLR

This is a small, anonymous, offline reference implementation of a certified
tabular regression workflow. It is intentionally independent of the
development repository: no experiment outputs, checkpoints, provider clients,
credentials, external datasets, or machine-specific paths are included.

The demo builds deterministic synthetic data, creates fixed train/working
validation/holdout/sealed-test partitions, fits preprocessing on the training
partition only, evaluates one local workflow, applies protocol checks, and
writes a compact certificate. The code is suitable for a clean reviewer
checkout and does not make network or provider calls.

## Quick start

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python run_demo.py --output outputs/demo
python -m pytest -q
```

The output directory is created on demand and is ignored by version control.
All paths in the package are relative to the checkout or are supplied through
the command line; no local workstation path is required.

## Package layout

- `vericell/data.py`: deterministic synthetic regression fixture.
- `vericell/splits.py`: fixed, disjoint partition construction.
- `vericell/workflows.py`: one deterministic local regression workflow.
- `vericell/certify.py`: protocol checks and violation reporting.
- `vericell/runner.py`: end-to-end offline execution and certificate writing.
- `run_demo.py`: command-line entry point.

This repository is a runnable code release, not a copy of historical result
artifacts. External data loaders and provider-backed experiments are outside
the release boundary.
