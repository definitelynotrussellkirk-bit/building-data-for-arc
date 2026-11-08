# 33d2674e3094

Three disconnected monochrome objects appear on a black canvas. Crop each object to its bounding box, sort the crops by **descending cell area**, break equal-area ties by bounding-box order `(top, bottom, left, right)`, then concatenate them left-to-right, top-aligned, with one black separator column.

The generator covers all three public shape profiles and all three public area patterns. Its scheduled curriculum alternates tied and untied areas, uses sparse crops whose bounding-box area disagrees with cell area, and assigns colors/positions so that scan-order, ascending/descending color-order, ascending-area, bbox-area, bottom-alignment, and color-based tie shortcuts are observably wrong. Every four consecutive examples remain identifiable after any one example is selected as the query.

Kind: `per_puzzle`. Reviewed version: `3.0.0`; rule pin: `9f849a344655`.
Approval is derived by the catalog from current code and retained evidence.
