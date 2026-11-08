# 91fd8c09b08e

0-bg grid (h ∈ 6-9, w ∈ 9-13) with: TARGET ∈ 2-4 ACTIVE ROWS picked at random; FOR EACH active row: (a) ONE COLOR-9 ANCHOR CELL at an INTERIOR column (2..w-3); (b) 1-2 COLORED OFF-AXIS CELLS — placed at random offsets 1..k from the anchor (where k = min(anchor, w-1-anchor) so reflections stay in-bounds), all on ONE SIDE of the anchor (sign chosen per row from {-1, +1}), painted in colors drawn from {1..8} (not 9). Inactive rows stay all-0. Rule (FOR EACH ROW WITH A 9-ANCHOR, MIRROR THE NON-9 COLORED CELLS ACROSS THE ANCHOR TO THE OPPOSITE SIDE): For EACH row r: FIND the color-9 cell (if any) at column ac. For EACH non-{0, 9} cell at (r, c): COMPUTE c' = 2*ac - c (reflection across the anchor column). IF c' is in-bounds AND g[r][c'] is 0: PAINT g[r][c'] with the same color as g[r][c]. Original cells, anchor, and other rows preserved. Net: each anchor row becomes horizontally symmetric across its 9-marker; colors are duplicated on both sides.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
