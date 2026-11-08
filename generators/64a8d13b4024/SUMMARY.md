# 64a8d13b4024

Count colors 1, 2, and 3 in a sparse 8–14 by 8–14 input. The label is a fixed 6×3 bottom-aligned bar chart whose three colored columns have those exact heights.

Kind: `per_puzzle`. Reviewed version: `2.1.0`. Rule hash: `e9d7e0db9b8a`.

## Reviewed contract

- Exact axes: `grid_h`, `grid_w` in 8–14 and `n1`, `n2`, `n3` in 1–6.
- Equal counts are lawful and are never rewritten.
- Unknown, mistyped, and out-of-range controls are rejected before generation.
- A period-3 curriculum puts count-six witnesses in two of every three positions, so every three-demo lesson and every held-out query rotation retains one.
- Declared canonical shortcut: cap every bar at height five. It fits all five canonical pairs and is refuted by each scheduled three-demo window.
- `workspace/reference_probe.py` provides an independent parser, oracle, rival, canonical check, determinism check, and distribution audit.

Focused verification: baseline 27 failed / 22 passed; repaired 50/50 passed. Independent audit: 180 samples in each of four bands, 720/720 valid and deterministic, all inputs distinct, and all 48 period/query rotations retained a cap-five refutation. The executable fixed-seed schedule receipt, strict override gate, and 32/32 Racket/oracle cross-check all passed.
