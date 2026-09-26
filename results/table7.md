# Table 7 — Category-to-invariant mapping

`S` means static, `D` dynamic, and `M` semantic.  This is a descriptive
contract mapping from the current manuscript.

| Audit category | Invariant | Stage | Instantiation |
|---|---|---|---|
| Split leakage | Split immutability, sealed test | S, D | `NI({te}; any non-final sink)` |
| Preprocessing leakage | Normalization and control scope | S | transform label restricted to training; `NI({ctrl}; input)` |
| Metric drift | Selection functional fixed | D | selection node computed under `E` |
| Target and perturbation leakage | Post-treatment exclusion | S | `NI({post, te}; model input)` |
| Batch shortcut | Plate shortcut prohibition | S | `NI({pid}; model input)` |
| Adaptive overfitting | Validation query budget | D | consumed budget `<= B`, audited answers only |
| Statistical misuse | Correction, effect size, interval | M | claim carries corrected `p`, effect size, interval |
| Provenance loss | Claim traceability | D, M | every reported number traces to a monitored node |
| Biological invalidity | Responsive feature source, dose | S, M | responsive mask is non-interfering; dose in support |

The anonymous package does not include the complete static fixpoint, runtime
monitor, or semantic-checker implementation needed to independently validate
this mapping.
