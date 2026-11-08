# f68fe53c1702 — all-marker bounding-box outline

Version 3.0.0; canonical Racket rule `ab8196a7d821`.

Draw the outline of the bounding box of all same-color nonzero markers on a fresh zero grid of the same size. Strictly interior markers disappear. Inputs use 2..7 distinct markers, height 4..24, width 5..24, and bbox span at least 3x3.

Default three-demonstration lessons mix one three-corner profile with two distributed-extrema profiles in a period-3 schedule. Rich examples refute using only the farthest marker pair and preserving interior input markers. Every one-of-four query holdout retains a rich demonstration for consecutive default indices.

Exact controls are `grid_h`, `grid_w`, `color`, and `num_cells`. Unknown/retired controls, non-integer values, and out-of-range values fail explicitly. See `notes.md` for domain limits and the source-bound review, `tests/` for regressions, and `workspace/` for reusable authoring probes.
