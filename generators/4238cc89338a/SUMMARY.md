# 4238cc89338a

A 0-background grid contains one connected blue (1) object and one connected red (2) object. Count blue cells in each row of the blue bounding box and red cells in each column of the red bounding box. The output is a small color-8 threshold intersection: output `(r, c)` is 8 exactly when column `c` is below the blue row count and row `r` is below the red column count.

Generator version 3.0.0 uses a strict constructive grammar with exact canvas/object-size overrides, canonical-size support, and an ordered three-demonstration curriculum. Its counterexample branch places an internal gap in a blue row so learners must count occupied cells rather than use the row's horizontal span. The declared shape grammar realizes 39 output matrices and maintains high input-placement diversity.

Kind: `per_puzzle`. Canonical rule hash: `e8d6ce4b7903`. Approval remains catalog-derived from integrated code and retained evidence.
