# Solve work log

## Exposure declaration

This is the required post-repair solve. I had already inspected and repaired the
assigned generator and canonical rule before this episode, so earlier rule
exposure is **yes**. During the solve episode itself I used only the visible
examples in `solve/challenge.json`, my own Python, and visible check feedback. I
did not reopen the generator, Racket rule, reference solutions, private labels,
or earlier solve explanations after `solve prepare`.

## Revision 0 — scaffold control

The prepared `solution.py` raised `NotImplementedError`. I wrote
`checks/post-solve-visible-test.py`, which imports only the visible challenge's
three training pairs and the candidate solution. The control run failed on the
first pair with that exception, confirming the test exercised the scaffold.
Receipt: `checks/post-solve-visible-test.red.log`.

## Visible pattern

In every training pair, colored cells form one or more hollow frames, sometimes
with a protruding stem and sometimes touching another frame. The output erases
all original colored cells and paints only the zero cells trapped inside each
frame, using that frame's color. Exterior zero cells remain zero. This suggests
a topological rule rather than a bounding-box rule: find four-connected zero
regions, reject any region reaching the grid edge, and paint each remaining
region with the color along its boundary.

## Revision 1 — enclosed-region flood fill

Implemented a four-neighbor flood fill over zero components. For each component
I record whether it touches an outer edge and count adjacent nonzero colors. An
enclosed component is painted with its most frequent boundary color; every other
cell stays zero. The frequency fallback is deterministic for a hypothetical
mixed boundary, although all visible holes have a single surrounding color.

This handles stems because they are merely erased boundary cells, handles edge
contact because exterior zero remains connected to the border, and handles
multiple/touching objects because each enclosed zero component is processed
independently. Remaining uncertainty is limited to unseen grids where one
single enclosed region is bounded by multiple colors; the examples do not show
such a case.
