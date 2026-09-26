
# VeriCell

## Protocol-Certified Workflow Search for Cellular Perturbation-Response Prediction

VeriCell is a framework for protocol-certified workflow search in cellular perturbation-response prediction. It integrates protocol contracts, static certification, runtime monitoring, audited validation, and semantic verification into a unified workflow-search pipeline.

This repository contains the VeriCell pipeline, an optional OpenAI-compatible LLM interface, experiment configurations, evaluation utilities, and results reported in the paper.

## Framework

VeriCell follows a unified workflow:

1. **Protocol Contract:** Define task-specific data, model, evaluation, and statistical constraints.
2. **Workflow Proposal:** Generate candidate workflows using an LLM provider.
3. **Static Certification:** Check candidate workflows against protocol invariants.
4. **Runtime Monitoring:** Enforce protocol constraints during execution.
5. **Audited Validation:** Evaluate candidates under a controlled validation policy.
6. **Semantic Verification:** Verify the correspondence between evaluation results and reported evidence.
7. **Certified Selection:** Admit certified candidates, select a workflow, and perform final evaluation.

The pipeline supports structured violation feedback and bounded candidate repair.

## Repository Structure

```text
vericell/                 Core VeriCell pipeline
configs/
  default.yaml            Default offline configuration
  paper/                  Experiment configurations
scripts/
  run_pipeline.py         Pipeline execution
  replay_results.py       Result-table verification
results/                  Manuscript results
data/                     Dataset information
docs/reproduction.md      Reproduction and environment details
tests/                    Unit and integration tests
run_demo.py               Lightweight offline demonstration
```

## Installation

Python 3.10 or newer is required.

```bash
python -m pip install -e .
```

## Quick Start

Run VeriCell using the deterministic offline provider:

```bash
python scripts/run_pipeline.py \
    --mode offline \
    --config configs/default.yaml \
    --output outputs/pipeline
```

The offline example exercises candidate generation, protocol certification, violation feedback, candidate repair, and final evaluation.

Execution records and certification results are saved to the specified output directory.

## LLM Provider

VeriCell includes an optional OpenAI-compatible interface for connecting external LLM providers.

Configure the provider through environment variables:

```bash
export VERICELL_LLM_BASE_URL="https://your-provider.example/v1"
export VERICELL_LLM_MODEL="your-model-id"
export VERICELL_LLM_API_KEY="your-api-key"
```

Run with the configured provider:

```bash
python scripts/run_pipeline.py \
    --mode live \
    --config configs/default.yaml \
    --output outputs/live
```

The default offline mode requires no external LLM service.

## Experiments and Results

Experiment configurations are organized in `configs/paper/`. The `results/` directory contains the tables reported in the manuscript.

| Table | Experiment | Result file |
|---|---|---|
| 1 | BBBC021 morphology prediction | `results/table1.csv` |
| 2 | LINCS L1000 perturbation prediction | `results/table2.csv` |
| 3 | Protocol violation auditing | `results/table3.csv` |
| 4 | Protocol contracts and invariants | `results/table4.md` |
| 5 | Verifier precision and recall | `results/table5.csv` |
| 6 | Audited adaptive validation | `results/table6.csv` |
| 7 | Violation-to-invariant mapping | `results/table7.md` |
| 8 | Certification-stage ablation | `results/table8.csv` |
| 9 | Backbone robustness | `results/table9.csv` |
| 10 | Full morphology benchmark results | `results/table10.csv` |

The result files preserve the manuscript-reported values. Their schemas and integrity can be checked using:

```bash
python scripts/replay_results.py --all
```

## Datasets

The experiments use publicly available cellular perturbation datasets:

- BBBC021
- BBBC036
- BBBC047
- CPG0016
- LINCS L1000

Dataset information and preparation instructions are provided in `data/README.md`.

## Tests

Run the test suite:

```bash
python -m pytest -q
```

The tests cover protocol checks, candidate admission and repair, provider response parsing, and offline pipeline execution.

For additional configuration and execution details, see `docs/reproduction.md`.
