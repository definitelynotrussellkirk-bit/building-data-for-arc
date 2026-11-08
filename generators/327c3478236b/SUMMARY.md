# 327c3478236b

0-bg grid (h ∈ 8-11, w ∈ 9-12) with: (a) ONE COLOR-3 SRC ANCHOR at a random position in the UPPER-LEFT region (rows 0..h//3, cols 0..w//2); (b) ONE COLOR-4 DST ANCHOR at a random position in the MIDDLE-RIGHT region (rows h//3..2h//3, cols w//2..w-1) — guarantees src and dst are distinct; (c) ONE COLOR-2 TEMPLATE BLOB — a 3-4 cell irregular blob built by grow_blob random walk, placed at a random non-overlapping position. Rule (COMPUTE THE VECTOR FROM SRC-3 TO DST-4, TRANSLATE THE COLOR-2 TEMPLATE BY THAT VECTOR; PAINT THE TRANSLATED COPY AS COLOR 8 ON A FRESH GRID, PRESERVING DST-4): FIND the COLOR-3 SRC cell at (sr, sc) and the COLOR-4 DST cell at (dr, dc); COMPUTE the vector v = (dr - sr, dc - sc). PRODUCE a fresh same-size grid of 0s. For EACH COLOR-2 template cell at (r, c): PAINT g[r + v.r][c + v.c] = COLOR 8 (cyan). ALSO PAINT the DST cell at (dr, dc) = COLOR 4 (preserving the anchor). Net: template gets translated by anchor-to-anchor vector, recolored to cyan, with dst anchor preserved as a 4-marker.

Kind: `per_puzzle`. Imported version: `2.0.2`.
Approval is derived by the catalog from current code and retained evidence.
