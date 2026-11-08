# 3f9bb51d528b

0-bg grid (h, w~8-13) with 2-4 SOLID 3×3 RINGS, each in a DISTINCT non-zero color. Each ring is an 8-cell hollow square: 3×3 bbox with the 8 perimeter cells painted in the ring's color and the CENTER cell at (r+1, c+1) initially 0. Rings are non-touching (1-cell padding from each other and grid edges). Rule: for EVERY 3×3 RING (8 cells of a single color forming a ring with a 0-cell center inside), IDENTIFY the CENTER cell (the unique 0-cell strictly inside the 3×3 bbox). FILL that center cell with the RING'S OWN color, completing the 3×3 into a SOLID monochrome 3×3 square. Net: each hollow ring becomes a solid 3×3 in its color; ring perimeters stay.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
