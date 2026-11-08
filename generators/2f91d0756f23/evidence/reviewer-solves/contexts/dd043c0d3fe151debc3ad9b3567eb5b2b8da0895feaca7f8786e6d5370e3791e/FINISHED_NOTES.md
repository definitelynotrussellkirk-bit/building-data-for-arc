# Solve work log

## Prior exposure

I had not opened this task's generator, Racket rule, reference solution, private
query labels, audit evidence, or prior solution explanations.  I used only the
visible examples printed by `review.py blind prepare` and the prepared README.

## Hypothesis

The color-1 cells form a unary count.  They are deleted in every output.  The
unique color-9 cell is a pivot.  All remaining nonzero cells are a seed motif
whose offsets from the pivot are copied through successive 90-degree clockwise
rotations.  A count of `k` color-1 cells requests rotations 0 through `k-1`, so
one marker leaves only the original motif, two markers add one clockwise copy,
and so on through four markers.

The examples support the same geometric rule:

- Example 1 rotates the offset `(-2,-1)` to `(-1,+2)`.
- Example 2 rotates both motif cells through 0, 90, and 180 degrees.
- Example 3 completes all four quarter turns for a multi-color motif.

The horizontal positions of the 1s do not appear to carry information; only
their number changes across the four demonstrations.

## Implementation and expected queries

`solution.py` copies the input, counts and erases every 1, locates the unique 9,
collects the original motif, and paints exactly the requested clockwise copies.
It rejects missing/multiple pivots, out-of-bounds copies, and conflicting
colored overlaps rather than silently guessing.

For query 0, one marker means delete the marker and retain the supplied 8/5
motif around 9.  For query 1, two markers mean also rotate the 3 at offset
`(+1,0)` to offset `(0,-1)`, adding a 3 immediately left of the 9.

Remaining uncertainty: unseen instances could theoretically encode direction in
the marker positions, but all four examples vary the positions while matching a
pure unary count, and the full 1-to-4 progression directly explains every output.
