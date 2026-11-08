# df53944d9b47

0-bg grid (h~6-14, w~8-16) with: (a) ONE COLOR-7 AXIS MARKER at column axis ∈ [2, w-3] (interior, with ≥1 col on each side), placed at random row axis_row ∈ [0, h-1] (cell (axis_row, axis) = 7); (b) 3-10 NON-BG NON-7 SOURCE CELLS placed at random distinct positions on EITHER side of the axis column (one side or scattered), each painted in a color cycling through a shuffled palette {1, 2, 3, 4, 5, 6, 8, 9}. For each source cell at (r, c), its mirror position (r, 2*axis-c) is bg-0 and in-bounds (constraint enforced). Rule (REFLECT EACH NON-BG NON-7 CELL ACROSS THE VERTICAL 7-AXIS COLUMN): find the COLOR-7 cell — its column is the AXIS. For EACH non-{0, 7} cell at (r, c) where c ≠ axis: COMPUTE the MIRROR position (r, 2*axis - c). PAINT the mirror cell with the SAME COLOR as the source (only if currently bg-0). The 7-axis marker and source cells stay. Net: every colored cell off the axis gets a mirror copy on the other side, producing left-right symmetry around the 7-axis.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
