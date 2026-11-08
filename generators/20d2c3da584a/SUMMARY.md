# 20d2c3da584a

0-bg grid (h~8-12, w~9-14) with 2-4 MONOCHROME CONNECTED COMPONENTS — each a 4-cell L-shape (or similar) chosen from a small shape bank, in a DISTINCT COLOR from {1..9} drawn per component. Components are placed at non-touching positions with 1-cell padding (8-conn buffer check). Each component has a non-trivial bbox (h × w = 3 × 2 / 3 × 3 / 2 × 3). Rule (PAINT EACH COMPONENT'S BBOX BORDER, KEEP ORIGINAL CELLS): For EACH MONOCHROME CONNECTED COMPONENT of color C with bbox (r1, c1, r2, c2): PAINT every cell on the BBOX OUTLINE (top row r1, bottom row r2, left col c1, right col c2 of the bbox) with color C. INTERIOR bg cells (strictly inside the bbox) STAY 0. The original component cells stay (they merge with the border paint). Net: each L-blob gains a rectangular outline around itself in its own color.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
