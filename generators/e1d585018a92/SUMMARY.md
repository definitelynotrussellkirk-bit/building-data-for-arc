# e1d585018a92

0-bg grid (h, w~9-14) with: (a) CELL (0, 0) holds the TARGET COLOR (a value in {1..9}); (b) ONE LARGEST TARGET OBJECT in the TARGET COLOR — a random connected polyomino (sizes 4-9, varied bbox) at random interior position; (c) optionally ONE SMALLER TARGET OBJECT (size 1..target_size-2) in the same color, strictly smaller; (d) 0-3 DISTRACTOR BLOBS in DISTINCT non-target colors, each strictly smaller than the target. All blobs with 1-cell padding. Output crops vary by random target shape, bbox, and color. Rule (CROP LARGEST TARGET-COLOR OBJECT TO BBOX): READ TARGET COLOR T = g[0][0]. Identify all OBJECTS in color T (excluding (0, 0)). Find the LARGEST. CROP to BBOX. EMIT the cropped subgrid. Net: (0, 0) names color; biggest object of that color is extracted.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
