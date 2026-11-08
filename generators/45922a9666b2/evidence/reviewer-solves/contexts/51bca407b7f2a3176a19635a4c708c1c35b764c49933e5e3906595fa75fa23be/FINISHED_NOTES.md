# Solve work log

## Exposure declaration before solving

I had not opened task `45922a9666b2`'s generator, Racket rule, notes, prior
solutions, audit records, or private labels.  I used only `challenge.json` and
local calculations over its visible train examples.

## Revision 1 — upward beams with one-cell right sidesteps

The bottom row contains several color-2 markers.  In every training pair, each
marker emits a vertical color-2 path toward the top while preserving all color-5
cells.  When a path's next upward cell is a 5, the path moves right on its current
row and tries upward again.  Repeated obstructions can create a horizontal run of
2s before the path finds a clear column.  If the immediate right cell is itself a
5 (or would leave the grid), the path terminates.

Concrete probes from the visible examples:

- Train 1, start column 4 rises to row 3, finds a 5 above, shifts to column 5,
  then reaches the top.  The start at column 7 shifts to column 8, rises once,
  then stops because its required right sidestep would land on a 5.
- Train 2, start column 5 must shift twice on row 2 because the cells above
  columns 5 and 6 are both 5; the output contains 2s at columns 5, 6, and 7 on
  that row.  Start column 7 stops because its first sidestep cell is a 5.
- Train 3, start column 0 is deflected to column 1 by a 5; start column 6 is
  later stopped when a sidestep would hit a 5.

I implemented this directly, copying the grid, using the original bottom-row 2s
as starts, and treating existing/painted 2s as traversable.  The main remaining
uncertainty is how two beams should interact if they merge; allowing shared 2
paths is the least destructive extension and does not alter any visible pair.
