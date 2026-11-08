# bbaef38af096

0-bg grid (h~9-11, w~11-13) with 3-4 SMALL MOTIFS (connected polyominoes of 3-5 cells each) scattered at distinct positions, each in a distinct non-bg color, with 4-adjacency isolation between motifs. Rule: ignore motif identity/shape and INSTEAD find the four EXTREMAL non-zero cells: NORTH (lowest row), SOUTH (highest row), WEST (leftmost col), EAST (rightmost col). Compute CENTER (cr, cc) = (midpoint of north/south rows, midpoint of west/east cols), and RADIUS = Manhattan distance from NORTH to CENTER. PAINT a blank canvas of the same dims, filling every cell whose Manhattan distance to (cr, cc) is ≤ RADIUS with color 8 (cyan). Net: the scattered colored motifs are replaced by a single cyan DIAMOND whose center and size are derived from the motifs' bounding extents.

Kind: `per_puzzle`. Imported version: `2.1.2`.
Approval is derived by the catalog from current code and retained evidence.
