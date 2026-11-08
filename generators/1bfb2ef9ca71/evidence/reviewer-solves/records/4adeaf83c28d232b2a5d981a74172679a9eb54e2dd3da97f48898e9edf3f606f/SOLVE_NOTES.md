# Visible-example work log

The three demonstrations preserve the grid size and erase the original sparse
markers except as part of newly drawn outlines. Every nonzero color appears
exactly twice. For each color, the two cells are on different rows and columns;
treating them as opposite corners of an axis-aligned rectangle exactly explains
the output.

Example 0 also fixes orientation ambiguity: color 3 uses the upper-left and
lower-right diagonal, while color 1 uses the upper-right and lower-left
diagonal. Both produce the same operation after sorting row and column bounds.
Example 1 shows three independent colors and a taller rectangle, so the rule is
not restricted to two objects or to three-row shapes. Example 2 confirms that
all other cells are cleared and only the hollow border is painted.

Implementation: collect positions by nonzero color; for each color with exactly
two diagonal endpoints, draw the top/bottom rows and left/right columns of its
bounding box on a fresh zero grid. The first implementation directly encodes
this hypothesis; no reference source or private answer was consulted during the
solve phase.
