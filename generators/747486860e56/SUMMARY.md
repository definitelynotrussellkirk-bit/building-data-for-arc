# 747486860e56

Version `4.1.0`; kind `per_puzzle`; canonical `RULE_HASH = 0ab2a183017a`.

On a zero-background grid, select the largest multicolor 8-connected nonzero component. Count every nonzero cell outside it, including cells in smaller touching components. If that residual count is K, paint a filled right triangle with leg K−1 at the residual corner. Its color is the residual plurality, with ties resolved by the earliest row-major occurrence among tied colors. Clear the residual cells, preserve the largest component in its original colors, then paint the triangle over any overlap.

The generated envelope has a uniquely largest component of at least four cells, 3–8 residual cells, exactly one residual corner, dimensions 6–24, and a triangle that fits in the grid. Exact controls are `grid_h`, `grid_w`, `corner`, and `n_markers`; unsupported or incompatible controls are rejected. Smaller residual components, color reuse, plurality ties, multicolor main objects, and triangle/main overlap are intentional.

The default curriculum uses six demonstrations. Profiles repeat with period three: a corner-vote scene, a tie where row-major order beats the maximum-color guess, and a tie where it beats the minimum-color guess. One seed fixes an episode's mono/multicolor and critical/neutral-corner context. Single-query holdouts of seven consecutively accepted default pairs are tested against the declared rivals; arbitrary seed mixing and exact-count override lessons are outside that claim.

See `notes.md`, `tests/`, `counterexamples/`, and `workspace/` for the current contract, regression evidence, and reusable receipt analyzer. Approval remains a catalog/maintainer decision; these notes do not grant it.
