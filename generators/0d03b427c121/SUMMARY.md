# 0d03b427c121

0-bg grid (h in 4..6, w sized to fit). ROW 0 is a MARKER STRIP: k color-1 (blue) cells encode TARGET AREA = k, m color-2 (red) cells encode TARGET BOUNDARY = m, scattered at random columns. Rows 1.. (the body) hold a RANDOM target polyomino whose (size, boundary-cell count) == (k, m), PLUS 1-3 distractor blobs with a DIFFERENT (size, boundary) pair, each a separate component. Rule: find the unique body blob with size==k AND boundary==m, crop it to its bbox and paint color 8 (cyan). The target SHAPE is random, so the OUTPUT varies; grid size, distractors, colors and all placements vary too (was a single fixed 2x4 blob → k=m=8).

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
