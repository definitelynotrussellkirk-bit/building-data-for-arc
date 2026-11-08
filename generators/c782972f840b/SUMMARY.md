# c782972f840b

A 0-background grid contains 4–6 isolated monochrome polyominoes using 2–3 nonzero colors. Objects are sorted by top-left position and compared by shape up to **rotation only**; reflected chiral shapes remain distinct. The output is an N×N relation matrix: diagonal 9; off-diagonal 6 for same rotation-shape and color, 4 for same rotation-shape only, 2 for same color only, and 0 for neither.

The default distribution covers all five canonical canvas/palette profiles and constructively includes a mirror-vs-rotation witness in every draw. Exact controls are `canvas_profile`, `n_objects` (4–6), and `relation_profile` (`with_duplicate` or `without_duplicate`).

Kind: `per_puzzle`. Selected version: `3.0.0`. Canonical rule hash: `1f9d3ac91fc0`.
Approval is derived by the catalog from current code and retained evidence.
