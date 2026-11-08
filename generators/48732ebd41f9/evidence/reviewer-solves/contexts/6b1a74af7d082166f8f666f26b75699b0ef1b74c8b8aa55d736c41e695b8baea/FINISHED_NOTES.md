# Post-repair visible-example solve notes

This is a reviewer-authored work log based only on `solve/challenge.json` during
the solve phase. I had already reviewed the generator and rule before this
phase, so this is deliberately **not** claimed as blind.

## Revision 1 — greatest-area solid zero rectangle

Across the four visible demonstrations, exactly one solid axis-aligned block of
zeros with at least two rows changes to color 6. Other zero runs remain zero.
The changed block is not consistently full-height, widest, or tallest:

- example 1 changes a 3×3 block rather than several wider-looking one-row runs;
- example 2 changes an interior 2×3 block;
- example 3 changes a 2×5 block in a two-row grid;
- example 4 changes a 2×4 block while preserving unrelated zeros and color 5.

The common selection criterion is greatest rectangle area among solid zero
rectangles of height at least two. I enumerate every top/bottom row band,
intersect its zero columns, split those columns into maximal contiguous runs,
and recolor the first maximum-area rectangle with 6. All other cells are copied.

No reference source, generator source, private labels, or Racket code was opened
while constructing this revision.
