# 5ae2936ffe21

0-bg grid (h, w~10-20) with 2-4 OBJECTS of strictly distinct sizes, each in a DISTINCT color drawn from 1..9. Object kinds from {rect, L_shape, cross, blob, line_h, line_v}; size progression linear or exponential; placement random/corners/row/column. Object sizes ascending; LARGEST object is unique (no ties). Rule (LARGEST → 2×2 COLOR OUTPUT): identify the LARGEST non-bg connected component (by cell count). EMIT a 2×2 OUTPUT GRID with every cell painted in the LARGEST OBJECT'S COLOR. Output dimensions are always 2×2; diversity is intrinsic-low (one shape per color, 9 colors total). Net: input has 2-4 differently-sized objects; output is a tiny 2×2 patch of the largest one's color.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
