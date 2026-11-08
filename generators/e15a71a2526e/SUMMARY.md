# e15a71a2526e

0-bg grid (h ∈ 7-14 / 5-18, w ∈ 8-16 / 6-20, by difficulty) with: (a) ONE HOLLOW COLOR-8 RECTANGULAR FRAME — fr × fc outline drawn at (r0, c0) with frame_size_kind ∈ {small / medium / large / wide / tall} (fr, fc both ≥4); position bias center (anchored) or spread (random); (b) 0-3 INTERIOR COLOR-8 NOISE CELLS — n_interior_8s additional 8-cells placed at random positions strictly inside the frame's bounding box (rows r0+1..r0+fr-2, cols c0+1..c0+fc-2). No color 2 in input. Rule (FIND ALL COLOR-8 CELLS' BBOX, FILL EVERY 0 INSIDE THAT BBOX WITH COLOR 2): COMPUTE the BOUNDING BOX of all color-8 cells (rmin, cmin, rmax, cmax). For EVERY (r, c) with rmin ≤ r ≤ rmax AND cmin ≤ c ≤ cmax: IF g[r][c] == 0: PAINT g[r][c] = COLOR 2 (red). Color-8 frame and interior 8s stay 8. Cells OUTSIDE the bbox stay 0. Net: the 8-frame's interior fills red; interior 8-noise cells punch holes in the red fill.

Kind: `per_puzzle`. Imported version: `2.3.0`.
Approval is derived by the catalog from current code and retained evidence.
