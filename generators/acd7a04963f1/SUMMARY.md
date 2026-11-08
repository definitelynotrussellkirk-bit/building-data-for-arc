# acd7a04963f1

0-bg grid (h, w~7-10) with: (a) cell (0, 0) holding a KEY COLOR from a 3-color palette; (b) ONE KEY-COLOR BLOB (2-4 cells, connected polyomino) placed AWAY from the (0, 0) corner in the same key color; (c) 1-2 DISTRACTOR BLOBS in the other 2 palette colors (2-3 cells each, non-overlapping). Rule: READ the KEY at (0, 0). Find the UNIQUE BLOB of matching KEY COLOR that's NOT at the corner. CROP that blob to its BBOX and OUTPUT the cropped subgrid (preserving key color and shape). Distractors and the corner-key are discarded. Net: corner-key selects the target by color; output is bbox crop of the matching non-corner blob.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
