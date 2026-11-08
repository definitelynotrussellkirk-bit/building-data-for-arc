# Visible-only solve log

This is a fresh solve from `solve/challenge.json`. I did not consult the Racket
rule, generator implementation, reference solution, private labels, or earlier
solution explanations during this phase. I had earlier rule exposure while
repairing the assigned generator, so the final disclosure must be `yes`.

## Revision 1 — diagonal corner bloom

All visible inputs contain solid monochrome 2×2 blocks on a zero background.
For each block whose top-left is `(r,c)`, the output preserves the block and
adds the same colour at `(r-1,c-1)`, `(r-1,c+2)`, `(r+2,c-1)`, and
`(r+2,c+2)` when those coordinates are in bounds. This accounts for clipped
blooms in training examples 0 and 2 as well as four-corner blooms in example 1.

Implementation details inferred from the examples:

- Detect source squares from the unchanged input, not from newly painted cells.
- Scan in row-major order.
- Copy before painting, preserve all source cells, and clip out-of-bounds targets.
- Write only into background so an earlier bloom would win an overlap.

No failed natural revision was needed; the first hypothesis explains every
visible changed cell and every unchanged boundary case.
