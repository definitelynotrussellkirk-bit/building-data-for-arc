# Visible-only post-repair solve log

This is a human-readable reasoning log, not a token-level model trace.

The four examples all contain one 2-cell and adjacent 3- and 4-cells.  Treat 2
as the origin.  The vector from 2 to 3 is the local horizontal/x direction; the
vector from 2 to 4 is the local vertical/y direction.  The 3x3 output represents
local coordinates x,y in {-1,0,1}, with output row y+1 and column x+1.  A cell is
8 exactly when the corresponding input position is 8.  The frame colors and
other colors are ignored.

Checks against visible examples:
- Example 0 has 3 left of 2 and 4 above 2, so the basis is rotated/reflected;
  projecting the four nearby 8s gives the displayed top row plus bottom-left.
- Examples 1–3 show additional distant or differently colored cells, but only
  local color-8 cells appear in the 3x3 output.

Implementation plan: locate unique 2,3,4; form the two unit vectors; inspect the
nine affine coordinates around 2; return 8 only for exact input color 8 and 0
otherwise.  Include bounds checks even though the examples keep the complete
window in bounds.
