# Solve work log

## Exposure statement before solving

I had not opened task `312fb4bdff00`'s generator, Racket rule, reference
solution, private labels, notes, or audit evidence. I used only the visible
examples in `challenge.json`/`README.md` and local Python calculations over
those visible grids.

## Revision 1 — transformed-twin detector and marker-anchored rendering

The 19 columns split into four 4-column panels separated by blue columns. The
lower four rows contain one monochrome shape per panel; the top row contains a
single marker. In every positive example, the shape in the first panel has a
translation/rotation/reflection-equivalent twin in one later panel. In the
negative example no later shape has the same dihedral shape signature, and the
answer is the 1x1 black grid.

For a positive example, the answer keeps the first panel's orientation, removes
its original translation, recolors it with the marker color, and places it on a
4x4 canvas. The bounding box is vertically lower-centred (`ceil((4-h)/2)`). Its
horizontal anchor is the marker column within a four-cell panel (`global_col %
5`), using the left middle cell for an even-width shape and clamping at the
canvas edge. This explains all observed shifts: the vertical domino moves to
column 3; the width-3 tetromino clamps at column 0; the 2x2 block starts at
column 2; and the width-3 pentomino starts at column 0.

I implemented canonical D4 matching with no task-specific colors or memorized
outputs. Remaining uncertainty: the visible examples do not show malformed
layouts, multiple markers, multiple shapes per panel, or multiple matching
later panels. The implementation treats all nonzero cells inside a panel as one
shape, uses the first marker, and only asks whether any later panel is a twin.
