# Table 4 — Protocol contract for the Cell Painting plate-based benchmark

The current manuscript lists thirteen invariants in four policy layers.  `S`
means static, `D` dynamic, and `M` semantic.

| Layer | Invariant | Stage | Instantiation |
|---|---|---|---|
| Data | Split immutability | S, D | `NI({te}; any non-final sink)` |
| Data | Normalization scope | S | fitted transform label is restricted to training |
| Data | Control reference scope | S | `NI({ctrl}; input)` |
| Model | Post-treatment exclusion | S | `NI({post, te}; model input)` |
| Model | Plate shortcut prohibition | S | `NI({pid}; model input)` |
| Evaluation | Selection functional fixed | D | selection node computed under `E` |
| Evaluation | Validation query budget | D | consumed budget `<= B` |
| Evaluation | Sealed test | D | `te` reached exactly once, after freeze |
| Evaluation | Claim traceability | D, M | every reported number traces to a monitored node |
| Statistics | Multiple-testing correction | M | comparative claim carries corrected `p` |
| Statistics | Effect size and interval | M | comparative claim carries both |
| Statistics | Responsive feature source | S | `NI({out}; responsive-mask definition)` |
| Statistics | Dose admissibility | M | dose lies within dataset support |

This file is a manuscript-aligned contract transcription.  It is not a claim
that the complete contract implementation is distributed in this repository.
