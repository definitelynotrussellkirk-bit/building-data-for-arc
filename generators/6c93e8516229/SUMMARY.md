# 6c93e8516229

A 0-background grid contains 3–8 pairwise separated green (`3`) tree components. For each 4-connected component, the canonical rule recolors it red (`2`) when it contains a degree-3 cell; otherwise magenta (`6`) when it has exactly two perpendicular degree-2 turns; otherwise blue (`1`). Degree-4 plus junctions and paths with three turns are therefore blue.

Generation uses 10–19 by 11–21 grids, supports exact `grid_h`, `grid_w`, and `component_count` controls, includes all three output classes on every board, and alternates explicit blue counterexamples to the two canonical-fitting shortcut rules. Canonical height/width/component-count profiles are weighted anchors rather than copied layouts.

Kind: `per_puzzle`. Current version: `3.0.2`. Canonical `RULE_HASH`: `6b0505b049ac`. The separate `workspace/parametric/` prototype proposes an episode-level `junction_degree ∈ {3,4}` extension; it does not alter canonical production behavior. Approval is derived by the catalog from current code and retained evidence.
