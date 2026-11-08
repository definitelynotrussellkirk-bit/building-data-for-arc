# Solve work log

## Exposure declaration before solving

I had not opened this task's generator, Racket rule, reference solution, private query labels, prior solution notes, or audit evidence. I used only the visible grids produced by `review.py blind prepare`.

## Revision 1 — diagnostic baseline

I deliberately ran the untouched template once to verify that the visible checker catches an unimplemented `solve`. It errored on all three visible examples, as expected. This was a diagnostic probe, not a proposed rule.

## Revision 2 — vertical gravity inside gray walls

### Observation and hypothesis

Color 5 forms complete horizontal and vertical walls. Within each vertical run of non-5 cells, every nonzero colored cell moves as far downward as possible while retaining its column and the top-to-bottom order of other colored cells in that same run. Zeros are empty space. A 5 cell blocks motion, so each wall-bounded vertical run is processed independently.

Concrete checks from the visible examples:

- Example 0, lower-left compartment, column 1: `[1,2,0,0]` becomes `[0,0,1,2]`.
- Example 0, lower-right compartment, column 5: `[6,2,0,0]` becomes `[0,0,6,2]`.
- Example 1, upper-left compartment, column 7: `[3,0,0]` becomes `[0,0,3]`.
- Example 2, upper-right compartment, column 7: `[6,1,0,0]` becomes `[0,0,6,1]`.

### Alternatives rejected

- Moving whole multi-cell objects rigidly does not fit: adjacent colored cells can separate vertically because gravity is column-wise.
- Sorting colors does not fit: their original vertical order is preserved.
- Horizontal gravity does not fit the many examples where only row positions change.
- Treating only complete rectangular rooms as units is unnecessary; the exact behavior is local to each contiguous non-wall segment in a column and also handles irregular wall layouts.

### Program

Copy the grid. For every column, split it at color-5 cells. In each segment, collect nonzero values in original order and rewrite the segment as enough zeros followed by those values.

### Remaining uncertainty

The visible data consistently identifies color 5 as the immovable wall and 0 as empty. I therefore keep those roles fixed rather than inferring them from frequency. The private queries may contain differently shaped wall compartments, but the segment-based implementation should generalize to them.
