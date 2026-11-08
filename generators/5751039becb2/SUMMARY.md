# 5751039becb2

Keep a nonzero cell exactly when at least one of its four diagonal neighbors has
the same color; erase every other cell. The version 3.0.0 sampler produces
6–10 by 7–12 sparse grids containing two to four distinct-color survivor
components. Each component is a diagonal pair or three-cell diagonal chain,
and every grid contains at least one three-cell chain plus at least one erased
contrast pattern.

A four-slot curriculum cycles:

1. a canonical-style unique singleton;
2. a remote singleton that reuses a surviving color;
3. a same-color orthogonal pair;
4. both counterexamples together.

Every three-demo cyclic window refutes the declared global-frequency,
whole-color, 8-neighbor, and exactly-two-occurrences rivals. Exact observable
overrides are `grid_h`, `grid_w`, `n_survivor_groups`, and `profile`.

Kind: `per_puzzle`. Reviewed version: `3.0.0`.
Canonical authority hash: `8626f391dcea`; the Racket rule was not changed.
Approval remains derived by the catalog from current code and retained evidence.
