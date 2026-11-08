# 46580cfcca75

Version `3.0.0`; canonical rule hash `001f318153f4`.

A 6–14 by 7–16 zero-background grid contains one or two separated,
distinct-color solid rectangles. At least one rectangle is at least 3×3, so
its interior visibly disappears; two slots in every four-sample schedule also
include a 2-cell-thick rectangle. The selected Racket rule redraws every
nonzero same-color object's tight bounding-box perimeter on a blank grid.

Exact public axes: `grid_h`, `grid_w`, and `n_rects`. Every Cartesian product
is constructive and recoverable from pixels with `observe_overrides`.
Three demonstrations are required. Four declared wrong rules—identity,
largest-only, drop-thin, and one global bounding box—are checked by the
semantic contract and the task-local lesson probe.

Kind: `per_puzzle`. Approval remains catalog/maintainer-owned.
