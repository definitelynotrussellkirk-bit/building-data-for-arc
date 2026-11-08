# 65dc463a7236

0-bg grid (h~8-10, w~9-12) with ONE CONNECTED OBJECT — a 4-connected 4-7 cell blob grown by random adjacency walk from a seed at (0, 0), with cells constrained to a 5×5 bbox around the seed (-2 ≤ dr ≤ 2, -2 ≤ dc ≤ 2). The blob is then NORMALIZED (shifted so top-left = (0, 0)) and PLACED at a random interior position (top, left) with INSET FROM BORDERS (top ∈ [1, h-obj_h-1], left ∈ [1, w-obj_w-1]) so the object sits at least 1 cell from the grid edges. The object is painted in a SINGLE non-0 color drawn from {1..9}. All other cells are bg-0. Rule (CROP TO THE BBOX OF THE SINGLE CONNECTED NON-ZERO OBJECT): COMPUTE the bbox of ALL non-zero cells in the input: (r1, c1, r2, c2). CROP the grid to that bbox: OUTPUT the subgrid rows r1..r2 × cols c1..c2 with the object's color preserved. The surrounding bg-0 padding is removed. Net: the input's tight bbox of the connected object is the output.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
