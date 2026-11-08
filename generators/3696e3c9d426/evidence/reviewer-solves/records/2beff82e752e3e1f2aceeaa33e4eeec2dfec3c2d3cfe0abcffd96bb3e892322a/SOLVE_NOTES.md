# Solve work log

## Exposure declaration before solving

I had not opened this task's generator, Racket rule, notes, reference solutions,
private labels, or audit records. I used only the visible examples produced by
`python3 review.py blind prepare` and the public `challenge.json`.

## Hypothesis

Each nonzero cell is an independent colored object affected by gravity toward the
bottom edge. Gravity acts separately in each column. All nonzero values in a
column are packed into the lowest available rows while preserving their original
top-to-bottom order. Zeros fill the vacated cells. The grid shape and every color
count remain unchanged.

Evidence across the visible examples:

- Example 0, column 2 has `2, 7, 4` from top to bottom and becomes `2, 7, 4`
  in rows 4–6. Column 0 similarly changes from `3` above `6` to those same two
  values in rows 5–6.
- Example 1, column 1 packs `5, 4, 1` into the bottom three rows without
  reordering them; column 5 packs `6, 2` into the bottom two rows.
- Example 2 repeats the same behavior independently in columns 1, 3, and 5.

I considered two alternatives: sorting by color value and moving the entire set as
one rigid object. Both are contradicted by the preserved per-column ordering and by
different columns falling different distances.

## Test-first probe

Before implementation, I imported the provided stub and asserted its output for
visible train example 0. It failed with `NotImplementedError`, confirming the
probe exercised the missing behavior rather than passing accidentally.

## Implementation

For each column, collect its nonzero values in row order, create an all-zero output
of the same shape, then place that sequence ending at the last row. This directly
implements the inferred invariant and handles empty columns and arbitrary grid
heights and widths.

## Remaining uncertainty

The visible examples consistently use color 0 as background and contain only
single-cell colored objects. The implementation therefore treats every nonzero
cell independently, which is the simplest rule fitting all evidence.
