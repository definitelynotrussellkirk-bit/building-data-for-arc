# 996fc37f49d9

A 0-background grid contains either two or three separated, monochrome, 4-connected components with strictly distinct cell counts. Rank all nonzero components by ascending area and repaint them on a blank grid: smallest to 2, next to 3, and (for three-component scenes) largest to 4. Input colour, position, and shape do not determine the rank.

Kind: `per_puzzle`. Imported version: `2.0.0`; current review candidate: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.

The review candidate broadens shapes, dimensions, placements and independent input palettes while retaining 50% canonical anchors. Default three-demo windows contain an explicit occupied-area versus bounding-box/scan-order diagnostic. Racket semantics are unchanged. See notes.md and workspace/README.md for source-bound checks and limitations.
