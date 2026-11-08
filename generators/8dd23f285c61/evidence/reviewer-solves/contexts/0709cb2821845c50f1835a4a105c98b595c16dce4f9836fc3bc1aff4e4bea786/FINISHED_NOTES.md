# Solve work log

## Exposure declaration

Before this solve I had not opened task `8dd23f285c61`'s generator, Racket rule,
notes, reference solution, private labels, or audit evidence. I used only the
visible examples printed by `python3 review.py blind prepare` and the public
`challenge.json`.

## Revision 1 — cardinal rays stopped by gray barriers

**Hypothesis.** Every red cell (2) is an emitter. Replace it with azure (8) and
extend azure rays north, south, west, and east to the grid edge, stopping before
the first gray cell (5) in each direction. Gray cells remain gray. Rays pass
through other red cells and overlapping rays merge.

**Visible evidence.** In train 0, the red at row 2, column 6 emits leftward only
through column 7 because gray at (2, 8) blocks its east ray, while its vertical
ray spans the grid. The other two emitters make full horizontal rows. Train 1
shows the same gray cell independently blocking the east ray of one emitter and
the north ray of another. Train 2 has long gray horizontal walls that truncate
all three vertical beams, plus a single gray cell that truncates one west beam.
The union exactly matches the visible outputs.

**Test-first probe.** A local visible-only regression covered all three training
pairs and a small case where a gray barrier blocks one ray but not the others.
It first failed on the untouched `NotImplementedError`, then passed after the
implementation. No query answers were consulted.

**Alternatives considered.** Drawing complete rows and columns without obstacle
handling fails wherever gray is aligned with an emitter. Treating gray as a
wall across its entire row or column fails because it blocks only a ray that
actually reaches the gray cell.

**Remaining uncertainty.** The examples consistently assign fixed semantic
roles to colors 2, 5, and 8, so the solver uses those colors directly.
