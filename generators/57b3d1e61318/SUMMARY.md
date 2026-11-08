# 57b3d1e61318

0-bg grid (h~9-12, w~11-14) with: (a) ONE COLOR-1 SOURCE ANCHOR at (ar1, ac1) (interior) surrounded by 3-4 COLOR-2 STENCIL CELLS at one of 5 hardcoded OFFSET PATTERNS (e.g., [(-1,0),(0,1),(1,0),(1,1)] etc.); (b) ONE COLOR-3 TARGET ANCHOR at (ar3, ac3) far from the source (≥2-cell radius padding) where the same offsets fit in-bounds. Rule (COPY COLOR-2 STENCIL FROM 1-ANCHOR TO 3-ANCHOR PRESERVING OFFSETS): identify the COLOR-1 SOURCE ANCHOR at (ar1, ac1) and its STENCIL OFFSETS = positions of COLOR-2 cells relative to it. Identify the COLOR-3 TARGET ANCHOR at (ar3, ac3). For EACH OFFSET (dr, dc) of color-2 cells, PAINT COLOR-2 at (ar3 + dr, ac3 + dc). Source + target anchors stay. Net: red stencil around 1-anchor replicates around 3-anchor with same shape.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
