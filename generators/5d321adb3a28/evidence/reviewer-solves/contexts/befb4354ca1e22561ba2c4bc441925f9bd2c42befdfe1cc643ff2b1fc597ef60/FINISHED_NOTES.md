# Solve notes

This is a human work log for the exposed post-repair solve. I had already seen the task rule during generator repair, so earlier exposure is **yes**; I did not consult the generator, Racket source, canonical ledger, prior solve directory, or private labels during this solve episode.

## Visible-example hypothesis

Across all three visible training pairs, the only edits are zeros exactly one cell between equal nonzero endpoints:

- `c 0 c` becomes `c c c` in a row.
- The same pattern becomes filled in a column.
- Unequal endpoints, longer gaps, and unrelated cells remain unchanged.

Implementation decision: scan the original input once, copy it, and fill a zero when its immediate horizontal pair or immediate vertical pair is equal and nonzero. Using the original grid avoids accidental iterative propagation.

## Revision 1

Implemented the direct local rule in `solution.py`. Expected all visible pairs to pass. No deliberate negative or diagnostic revision was created.
