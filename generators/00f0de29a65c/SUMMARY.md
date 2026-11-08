# 00f0de29a65c

A zero-background grid contains one isolated singleton marker and 2–4 distinct-color sparse polyominoes. Select the multi-cell component with the smallest cell count; break ties by bounding-box top row and then left column. Crop the selected component's raw bounding box, recolor its nonzero cells to the marker color, and upscale both axes by two.

Kind: `per_puzzle`. Reviewed version: `3.1.0`. Canonical `RULE_HASH`: `708518128a6f`.

The default four-example curriculum cycles through `unique_min`, `two_way_tie`, `all_tied`, and `two_way_tie`. Unique minima rotate through all four quadrants; tied-minimum examples place a larger distractor earlier in scan order. This makes size selection and the positional tie-break visible without binding a semantic profile to a fixed location.

Exact public axes are `grid_h` (10–18), `grid_w` (11–18), `n_shapes` (2–4), and `texture` (`unique_min|two_way_tie|all_tied`). `texture=two_way_tie,n_shapes=2` is the sole declared incompatibility. Final-grid validation, an independent Python rule mirror, executable rivals/witnesses, and a source-bound 100-lessons-per-band census are retained with the task.
