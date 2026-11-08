# Solve work log

Earlier exposure: none to task `48fee61713bb`'s generator, rule, solutions, labels, or prior notes. I read only `solve-blind/challenge.json` after preparation.

## Revision 1 — tile compression plus clockwise edge gravity

The 30×30 input contains hollow 3×3 colored frames on a four-cell lattice. One complete edge is color 1. Compressing each frame to one colored cell and deleting the empty middle separator lane gives either a 6×7 or 7×6 symbolic grid.

Across the three visible examples, the color-1 edge specifies motion tangent to the border in clockwise order: top → right, right → down, bottom → left, left → up. Within each row or column, nonzero tile order is preserved while empty cells move to the opposite side. I verified this manually on several columns/rows: for example, the first right-edge training column `[0,6,6,0,0,8]` becomes `[0,0,0,6,6,8]`, exactly matching the output.

Probe: a local test imports `solution.py` and compares `solve` against all three visible training outputs. The initial stub failed with `NotImplementedError`, as expected. Revision 1 implements the compact-lattice extraction and four gravity directions. Remaining uncertainty: the border-to-direction mapping is inferred from three sides; the unseen top-side case is the only extrapolated member, completed by the consistent clockwise cycle.
