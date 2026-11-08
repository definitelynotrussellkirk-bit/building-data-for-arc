# 1c6e46cc5aca

15×17 grid with 3-4 rectangular OUTLINES, each in a distinct non-zero color. Outlines are nested (largest outermost) so the interruption-topology sort is well-defined: each outline's bbox contains the next-smaller outline's bbox. Outline = rectangle border only (interior is 0 / inner outlines). Rule: detect each color's outline rectangle. Compute interruption topology — outline A interrupts B if A's outline crosses any of B's edge cells. Topologically sort colors so interrupters come first (outermost). Output: (2n-1) × (2n-1) square where n = number of colors. Build concentric layers using distance-to-edge: layer k (0=outermost) gets the k-th color in the sort. Output cell at (r, c) = colors[min(r, c, size-1-r, size-1-c)].

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
