# 65a142eb4d9b

Version `3.0.0`; Racket rule hash `7224a7556e4b`.

On a black grid, every nonzero cell with no same-color **cardinal** neighbor expands into a same-color plus (center plus every in-bounds cardinal neighbor). Cells belonging to a same-color cardinal component remain unchanged. Expansion eligibility is computed from the original input.

The linked curriculum uses three demonstrations and a six-slot deterministic schedule. Canonical profiles preserve sparse distinct interior dots; isolation profiles add a blocked same-color domino plus a remote singleton; diagonal-edge profiles add same-color diagonal singletons and a border singleton. Every three consecutive scheduled examples contain all three roles, refuting canonical-fitting shortcuts based on global uniqueness, 8-connectivity, interior-only expansion, or expanding every nonzero cell.

Exact public axes are `grid_h` 7..10, `grid_w` 7..10, `n_expandable_cells` 1..5, and `n_blocked_dominoes` 0..1. The validator enforces a narrow conflict-free teaching grammar.

Kind: `per_puzzle`. Approval is derived by the catalog from current code and retained evidence.
