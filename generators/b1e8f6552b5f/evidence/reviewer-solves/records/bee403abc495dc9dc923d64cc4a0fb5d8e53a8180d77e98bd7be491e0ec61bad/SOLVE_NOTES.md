# Solve work log

## Exposure before solving

I had not opened the generator, Racket rule, reference solutions, private labels,
or earlier explanations for task `b1e8f6552b5f`. I had only read the packet's
workflow instructions and the visible examples printed by `blind prepare`.

## Revision 1 — hollow-square expansion

**Hypothesis.** Every nonzero input cell is a marker for the center of a hollow
3×3 square in the same color. The original center becomes background and the
eight neighboring cells become the marker color.

**Evidence from visible examples.** In train example 0, the markers at `(3,1)`
and `(3,5)` become two disjoint 3×3 perimeters at rows `2..4`. Train example 1
shows the same transformation with two colors and different rows/columns. Train
examples 2 and 3 repeat it with three and four markers, preserving each marker's
color. All visible markers are at least one cell from the grid edge and the
visible perimeters do not conflict.

**Probe.** I first ran a small public-example test against the untouched skeleton;
it failed with `NotImplementedError`, confirming the test exercised the missing
behavior. I then implemented the point-to-perimeter transformation using a
snapshot of the original nonzero cells.

**Alternatives considered.** The output could be described as replacing each
point with its eight-neighborhood, or as drawing a hollow 3×3 box. These are
equivalent on the visible data. I did not infer any color-specific behavior.

**Remaining uncertainty.** The examples do not specify conflict resolution for
overlapping squares of different colors. The implementation paints markers in
row-major order, but all displayed examples and queries have disjoint perimeters.
It clips at grid boundaries defensively, although visible markers have a full
one-cell margin.
