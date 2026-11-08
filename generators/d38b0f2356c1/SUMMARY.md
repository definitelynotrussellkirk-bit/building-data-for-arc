# d38b0f2356c1

An 11×11 gray lattice contains nine 3×3 blocks. Exactly one block has no
cyan (8); treat its nine cells as a 3×3 macro-template, expanding each cell to
the corresponding solid 3×3 output region while preserving gray separators.

The v2.1.0 sampler retains canonical-density examples and schedules two
counterexample profiles in every three consecutive draws: one reverses the
canonical density ordering, and one gives all nine blocks equal occupied-cell
counts. These refute the canonical-fitting “sparsest block” and “unique
occupied-count outlier” shortcuts while keeping the intended no-cyan rule stable.

Kind: `per_puzzle`. Reviewed version: `2.1.0`.
Approval remains derived by the catalog from current code and retained evidence.
