# 7160d1eda94b

0-bg grid (h ∈ 8-20, w ∈ 7-18, by difficulty) with: TARGET ∈ 2-9 COMPONENTS, each in a DISTINCT color drawn from {1..9}, where: (a) the BOTTOM-MOST COMPONENT is placed at br = h - sh (bottom-aligned) with sh × sw drawn from bottom_shapes bank (L-tromino, corner, 2×2, L-tet, I-tro horizontal/vertical), painted in colors[0]; (b) OTHER components placed STRICTLY ABOVE br (rows ≤ br - 1) with 1-cell padding, drawn from a wider other_shapes bank. Guaranteed: ONE component has STRICTLY LOWEST bottom row. Rule (KEEP ONLY THE COMPONENT WHOSE BBOX BOTTOM ROW IS STRICTLY THE LOWEST; ERASE ALL OTHER COMPONENTS TO 0; KEPT COMPONENT PRESERVES SHAPE AND COLOR): EXTRACT every 4-connected non-bg component. For each: COMPUTE bbox-bottom-row. FIND the MAXIMUM bottom row (strictly unique). PRODUCE a fresh same-size grid of 0s. PAINT only the bottommost component's cells in its original color. Net: the lowest component wins; others vanish.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
