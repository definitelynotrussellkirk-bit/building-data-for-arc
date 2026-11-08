# Solve work log

## Prior exposure

I had already read the assigned generator and canonical rule while performing the
repair, so this is an **exposed** post-repair solve, not a blind solve. During
this solve phase I did not reopen the generator, Racket source, reference
solutions, private labels, or prior solution explanations; I used the prepared
visible examples only.

## Revision 1 — row-local left slide

Across the four demonstrations, every row containing color 3 has one contiguous
horizontal block. Its length and all non-3 cells are preserved. The block moves
left until its first cell is immediately to the right of the nearest color-8
cell originally to its left. With no color 8 to its left, it starts at column 0.
Colors 5, 7, and 9 do not act as barriers: in example 1's last row the two 3s
move across the 9 to columns 0–1, and in example 2 the length-three block moves
across the 5 to columns 0–2. Color-8 cells to the right of a block are irrelevant.

Implementation plan: copy the grid, find each row's contiguous 3-block, compute
`destination = 1 + max(leftward 8 columns)` with a default of 0, clear the old
block, and write the same number of 3s at the destination. Rows without 3s are
unchanged. Remaining uncertainty is limited to inputs with multiple disjoint
3-blocks in one row, which are absent from all visible examples.
