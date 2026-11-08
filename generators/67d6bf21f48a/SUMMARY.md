# 67d6bf21f48a

0-bg grid (h~8-11, w~9-12) with 2-3 BLOBS — each a 2-4 cell 4-connected blob grown via grow_blob, painted in a DISTINCT non-0 color drawn from {1..9}. Blobs are placed at non-touching positions with non-overlapping bboxes (tracked in used set). Each blob has bbox ≥ 2×2 (size ≥ 2 ensures the checker pattern is visible). Rule (FILL EACH BLOB'S BBOX WITH A CHECKER PATTERN IN THE BLOB'S COLOR): for EACH 4-CONNECTED non-bg blob of color C: COMPUTE its bbox (r1, c1, r2, c2). For EACH cell (r, c) in the bbox: PAINT (r, c) with COLOR C if (r + c) parity matches the bbox's top-left parity (checker pattern starting with C at (r1, c1)); ELSE leave as bg-0. The original blob cells are absorbed into the checker fill. Net: each irregular blob inflates into a checker pattern within its bbox, in its color.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
