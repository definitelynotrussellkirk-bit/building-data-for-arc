# 629901f9cf30

Every nonzero input cell is a seed. Each output cell takes the color of its unique nearest seed by Manhattan distance; cells tied between different nearest colors remain 0.

Kind: `per_puzzle`. Reviewed version: `3.0.0`. Rule hash: `96013a689278`.

## Reviewed contract

- Exact axes: `grid_h`, `grid_w` in 4–18 and `n_seeds` in 2–6.
- Every generated scene constructively includes a genuine nearest-color tie.
- Default lessons use a period-3 schedule of 3, 4, and 6 seeds; every three-demo window therefore refutes a “first three seeds only” solver.
- Seed colors are distinct nonzero ARC colors, and all controls are strict in every difficulty band.
- Named rivals cover both canonical-fitting seed truncation and the incorrect policy of choosing the lowest color on ties.
- `workspace/reference_probe.py` supplies an independent Manhattan oracle, tie detector, rivals, canonical verification, distribution audit, and exhaustive period/query-rotation check.

Focused verification: baseline 24 failed / 17 passed; repaired 41/41 passed. Independent audit: 180 samples in each of four bands, 720/720 valid, deterministic, distinct, and tie-bearing; all 48 period/query rotations refuted both declared rivals. The executable fixed-seed schedule receipt, strict override gate, and 26/26 Racket/oracle cross-check passed.
